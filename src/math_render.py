import base64
import io
import re

import matplotlib.pyplot as plt


def render_latex_to_data_uri(latex, fontsize=14):
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, f"${latex}$", fontsize=fontsize)

    buffer = io.BytesIO()

    fig.savefig(
        buffer,
        format="png",
        dpi=200,
        transparent=True,
        bbox_inches="tight",
        pad_inches=0.05,
    )

    plt.close(fig)

    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")

    return f"data:image/png;base64,{encoded}"


def replace_latex(text):
    # Display math: $$ ... $$
    text = re.sub(
        r"\$\$(.+?)\$\$",
        lambda m: (
            '<div style="text-align:center;margin:16px 0;">'
            f'<img src="{render_latex_to_data_uri(m.group(1))}" '
            'style="max-width:100%;height:auto;">'
            '</div>'
        ),
        text,
        flags=re.DOTALL,
    )

    # Inline math: $ ... $
    text = re.sub(
        r"\$(.+?)\$",
        lambda m: (
            f'<img src="{render_latex_to_data_uri(m.group(1), fontsize=12)}" '
            'style="vertical-align:middle;">'
        ),
        text,
    )

    return text