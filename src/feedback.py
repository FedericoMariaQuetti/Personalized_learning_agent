"""
feedback.py
-----------
Sezione 7 (Feedback), lato "lettura": si collega a Gmail via IMAP, cerca
le tue risposte non lette alla newsletter, chiede all'AI di interpretarle
in un formato strutturato (JSON) e applica solo modifiche a campi noti e
validati dello stato — mai testo libero non controllato.

Ogni modifica applicata viene registrata in state["feedback_log"], così la
puoi rivedere nel resoconto settimanale.
"""

import email
import email.utils
import imaplib
import json
from datetime import date

from copy import deepcopy
from llm import generate_text

TRACK_DAYS = {"breve": 5, "completa": 10, "media": 20}


def process_feedback(state, gmail_user, gmail_password, allowed_senders):
    """
    Legge il feedback nuovo e lo applica.

    Le email vengono marcate come lette solo dopo che:
      1. il feedback è stato interpretato;
      2. il patch è stato applicato con successo;
      3. la marcatura come letta è andata a buon fine.

    Se uno di questi passaggi fallisce, lo stato originale viene mantenuto
    e il feedback potrà essere ritentato nella prossima esecuzione.
    """
    feedback_items = _fetch_unread_feedback(
        gmail_user,
        gmail_password,
        allowed_senders,
    )

    if not feedback_items:
        return state

    feedback_texts = [item["body"] for item in feedback_items]
    message_ids = [item["message_id"] for item in feedback_items]

    combined_text = "\n\n---\n\n".join(feedback_texts)

    # Lavoriamo su una copia: se qualcosa fallisce, lo stato originale
    # passato da main() non viene modificato.
    working_state = deepcopy(state)

    patch = _interpret_feedback(working_state, combined_text)

    # JSON non interpretabile: non consideriamo il feedback elaborato.
    if patch is None:
        print("   ⚠ Impossibile interpretare il feedback: nessuna modifica applicata.")
        return state

    working_state = _apply_patch(working_state, patch)

    # Segniamo le email come lette SOLO dopo aver applicato con successo
    # il feedback.
    _mark_feedback_as_read(
        gmail_user,
        gmail_password,
        message_ids,
    )

    # A questo punto possiamo rendere ufficiale il nuovo stato.
    return working_state

# --- Lettura email via IMAP -------------------------------------------------

def _fetch_unread_feedback(gmail_user, gmail_password, allowed_senders):
    allowed = {addr.strip().lower() for addr in allowed_senders}

    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(gmail_user, gmail_password)

    try:
        mail.select("INBOX")

        status, data = mail.search(None, "UNSEEN")
        ids = data[0].split() if status == "OK" and data and data[0] else []

        feedback_items = []

        for msg_id in ids:
            status, msg_data = mail.fetch(msg_id, "(BODY.PEEK[])")

            if status != "OK" or not msg_data or not msg_data[0]:
                continue

            msg = email.message_from_bytes(msg_data[0][1])

            from_address = email.utils.parseaddr(
                msg.get("From", "")
            )[1].lower()

            if from_address not in allowed:
                continue

            body = _extract_text_body(msg)
            body = _strip_quoted_reply(body)

            if body.strip():
                feedback_items.append({
                    "message_id": msg.get("Message-ID", ""),
                    "body": body.strip(),
                })

        return feedback_items

    finally:
        try:
            mail.close()
        except Exception:
            pass

        try:
            mail.logout()
        except Exception:
            pass


def _mark_feedback_as_read(gmail_user, gmail_password, message_ids):
    """
    Marca come lette solo le email che sono state effettivamente elaborate.
    Usa Message-ID per evitare di dipendere dai sequence number IMAP
    della precedente connessione.
    """
    if not message_ids:
        return

    wanted = {mid for mid in message_ids if mid}

    if not wanted:
        return

    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(gmail_user, gmail_password)

    try:
        mail.select("INBOX")

        status, data = mail.search(None, "UNSEEN")
        ids = data[0].split() if status == "OK" and data and data[0] else []

        for msg_id in ids:
            status, msg_data = mail.fetch(msg_id, "(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)])")

            if status != "OK" or not msg_data or not msg_data[0]:
                continue

            header = email.message_from_bytes(msg_data[0][1])
            message_id = header.get("Message-ID", "")

            if message_id in wanted:
                mail.store(msg_id, "+FLAGS", "\\Seen")

    finally:
        try:
            mail.close()
        except Exception:
            pass

        try:
            mail.logout()
        except Exception:
            pass


def _extract_text_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition", ""))
            if content_type == "text/plain" and "attachment" not in disposition:
                charset = part.get_content_charset() or "utf-8"
                payload = part.get_payload(decode=True)
                return payload.decode(charset, errors="replace") if payload else ""
        return ""
    charset = msg.get_content_charset() or "utf-8"
    payload = msg.get_payload(decode=True)
    return payload.decode(charset, errors="replace") if payload else ""


def _strip_quoted_reply(text):
    """Taglio euristico della parte 'citata' delle email di risposta (best-effort)."""
    markers = ["\nIl ", "\nOn ", "\n> ", "-----Original Message-----", "\nDa: ", "\nFrom: "]
    positions = [text.find(m) for m in markers if text.find(m) != -1]
    return text[:min(positions)].strip() if positions else text.strip()


# --- Interpretazione via AI -------------------------------------------------

INTERPRET_PROMPT = """Sei un sistema che interpreta il feedback di uno studente su un percorso
di apprendimento personalizzato e lo traduce in istruzioni strutturate.

Stato attuale (per riferimento, per capire a cosa si riferisce lo studente):
- Science: argomenti attivi: {science_topics}
- Reading: libro attuale: {book}
- Philosophy: filosofo attuale: {philosopher}
- German: livello attuale: {german_level}

Messaggio/i di feedback ricevuti dallo studente:
---
{feedback_text}
---

Rispondi SOLO con un oggetto JSON valido (nessun testo fuori dal JSON), omettendo
le chiavi non rilevanti al feedback ricevuto. Struttura:

{{
  "science": {{
    "add_or_replace_topic": {{"target": "nome argomento da sostituire, o null se è uno slot concluso", "new_name": "...", "track": "breve|completa|media"}},
    "adjust_track": {{"topic_name": "...", "new_track": "breve|completa|media"}},
    "note": "..."
  }},
  "reading": {{"next_book": "...", "note": "..."}},
  "philosophy": {{"next_philosopher": "...", "note": "..."}},
  "german": {{"level": "...", "note": "..."}},
  "coding": {{"note": "..."}},
  "poker": {{"note": "..."}},
  "general_note": "..."
}}
"""


def _interpret_feedback(state, feedback_text):
    prompt = INTERPRET_PROMPT.format(
        science_topics=", ".join(t["name"] for t in state["science"]["topics"]),
        book=state["reading"]["book"],
        philosopher=state["philosophy"]["philosopher"],
        german_level=state["german"]["level"],
        feedback_text=feedback_text,
    )
    raw = generate_text(prompt, json_mode=True)
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


# --- Applicazione delle modifiche (whitelist di campi noti) -----------------

def _apply_patch(state, patch):
    changes = []
    today = date.today().isoformat()

    if "science" in patch:
        changes += _apply_science_patch(state["science"], patch["science"])

    if "reading" in patch:
        changes += _apply_simple_patch(
            state["reading"], patch["reading"], section_label="Reading",
            title_field="book", next_field="next_book", reset_fields=["day_in_block"],
        )

    if "philosophy" in patch:
        changes += _apply_simple_patch(
            state["philosophy"], patch["philosophy"], section_label="Philosophy",
            title_field="philosopher", next_field="next_philosopher", reset_fields=["day_in_block"],
        )

    if "german" in patch:
        german_patch = patch["german"]
        if german_patch.get("level"):
            state["german"]["level"] = german_patch["level"]
            state["german"]["progress_notes"] = ""
            changes.append(f"German: livello aggiornato a {german_patch['level']}")
        if german_patch.get("note"):
            state["german"]["progress_notes"] += f"\nNota da feedback: {german_patch['note']}"
            changes.append(f"German: nota aggiunta ({german_patch['note']})")

    for section in ("coding", "poker"):
        if section in patch and patch[section].get("note"):
            note = patch[section]["note"]
            state[section]["progress_notes"] = (state[section].get("progress_notes", "") + f"\nNota da feedback: {note}").strip()
            changes.append(f"{section.capitalize()}: nota aggiunta ({note})")

    if patch.get("general_note"):
        changes.append(f"Nota generale registrata: {patch['general_note']}")

    for change in changes:
        state["feedback_log"].append({"date": today, "change": change})

    return state


def _apply_science_patch(science_state, science_patch):
    changes = []

    if science_patch.get("note"):
        for topic in science_state["topics"]:
            if topic["day"] <= topic["track_days"]:  # solo argomenti ancora attivi
                topic["progress_notes"] += f"\nNota da feedback: {science_patch['note']}"
        changes.append(f"Science: nota aggiunta a tutti gli argomenti attivi ({science_patch['note']})")

    if "adjust_track" in science_patch:
        target = science_patch["adjust_track"].get("topic_name", "").lower()
        new_track = science_patch["adjust_track"].get("new_track")
        if new_track in TRACK_DAYS:
            for topic in science_state["topics"]:
                if target in topic["name"].lower():
                    topic["track"] = new_track
                    topic["track_days"] = TRACK_DAYS[new_track]
                    changes.append(f"Science: '{topic['name']}' spostato sul ritmo '{new_track}'")

    if "add_or_replace_topic" in science_patch:
        info = science_patch["add_or_replace_topic"]
        new_name = info.get("new_name")
        new_track = info.get("track")
        target = (info.get("target") or "").lower()

        if new_name and new_track in TRACK_DAYS:
            slot_index = None
            if target:
                for i, topic in enumerate(science_state["topics"]):
                    if target in topic["name"].lower():
                        slot_index = i
                        break
            else:
                for i, topic in enumerate(science_state["topics"]):
                    if topic["day"] > topic["track_days"]:  # primo slot concluso
                        slot_index = i
                        break

            if slot_index is not None:
                old_name = science_state["topics"][slot_index]["name"]
                science_state["topics"][slot_index] = {
                    "name": new_name,
                    "track": new_track,
                    "track_days": TRACK_DAYS[new_track],
                    "day": 1,
                    "progress_notes": "",
                    "special_instructions": "",
                }
                changes.append(f"Science: '{old_name}' sostituito con '{new_name}' ({new_track})")

    return changes


def _apply_simple_patch(section_state, section_patch, section_label, title_field, next_field, reset_fields):
    changes = []
    if section_patch.get(next_field):
        old_title = section_state[title_field]
        section_state[title_field] = section_patch[next_field]
        section_state["progress_notes"] = ""
        for field in reset_fields:
            section_state[field] = 1
        changes.append(f"{section_label}: '{old_title}' sostituito con '{section_patch[next_field]}'")
    if section_patch.get("note"):
        section_state["progress_notes"] += f"\nNota da feedback: {section_patch['note']}"
        changes.append(f"{section_label}: nota aggiunta ({section_patch['note']})")
    return changes
