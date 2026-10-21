#!/usr/bin/env python3

from pathlib import Path
from bs4 import BeautifulSoup
import re

INPUTS = {
    "MR B & Me": "data/mrbnme/page.html",
    "Ballstaviken": "data/ballstaviken/page.html",
}

OUTPUT = "data/restaurant_content.txt"


def html_to_text(html):
    soup = BeautifulSoup(html, "html.parser")

    # Remove non-content elements
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator="\n")

    # Normalize whitespace
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


with open(OUTPUT, "w", encoding="utf-8") as out:
    for name, path in INPUTS.items():
        html = Path(path).read_text(encoding="utf-8", errors="ignore")
        text = html_to_text(html)

        out.write(f"===== {name} =====\n")
        out.write(text)
        out.write("\n\n")

print(f"Wrote {OUTPUT}")
