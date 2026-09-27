"""
state.py
--------
Legge e salva data/curriculum_state.json, il file che ricorda a che
punto sei in ogni materia. Ogni sezione (science, reading, ecc.) legge
e modifica solo la sua "fetta" di questo dizionario.
"""

import json
import os

STATE_PATH = "data/curriculum_state.json"


def load_state(path=STATE_PATH):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state, path=STATE_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
