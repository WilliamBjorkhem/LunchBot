#!/usr/bin/env python3

from pathlib import Path
from bs4 import BeautifulSoup
import json
import re

RESTAURANTS_FILE = "restaurants.json"
OUTPUT = "data/restaurant_content.txt"


def html_to_text(html):
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator="\n")

    text = re.sub(r"\n\s*\n+", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


restaurants = json.loads(
    Path(RESTAURANTS_FILE).read_text(
        encoding="utf-8"
    )
)

Path("data").mkdir(exist_ok=True)

with open(OUTPUT, "w", encoding="utf-8") as out:
    for restaurant in restaurants:
        name = restaurant["displayName"]
        html_file = (
            f"data/{restaurant['name']}/page.html"
        )

        path = Path(html_file)

        if not path.exists():
            print(f"Skipping {name}: {html_file} not found")
            continue

        html = path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        text = html_to_text(html)

        out.write(f"===== {name} =====\n")
        out.write(text)
        out.write("\n\n")

print(f"Wrote {OUTPUT}")
