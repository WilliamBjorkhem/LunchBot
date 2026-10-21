#!/usr/bin/env python3

import json
import os
from pathlib import Path

from google import genai
from google.genai import types

client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

DATA_DIR = REPO_ROOT / "data"
OUTPUT_FILE = REPO_ROOT / "menus.json"

MODELS = [
    "gemini-3.8-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite"
]

if not DATA_DIR.exists():
    raise RuntimeError(
        f"Data directory not found: {DATA_DIR}"
    )

RESTAURANTS_FILE = SCRIPT_DIR / "restaurants.json"

restaurant_config = {
    entry["name"]: entry
    for entry in json.loads(
        RESTAURANTS_FILE.read_text(
            encoding="utf-8"
        )
    )
}

PROMPT = """
Extract today's lunch menu from all supplied content.

Use ALL provided files:
- HTML
- PDFs
- Images

Return ONLY valid JSON.

Expected format:

{
  "name": "",
  "lunchMenu": [
    {
      "name": "",
      "description": ""
    }
  ]
}

Rules:
- name must contain the restaurant name.
- lunchMenu must contain all lunch dishes found.
- description may be empty if no description exists.
- Do not include dates.
- Do not include markdown.
- Do not include explanations.
- Do not wrap JSON in code fences.

If no menu is found:

{
  "name": "",
  "lunchMenu": []
}
"""

SUPPORTED_EXTENSIONS = {
    ".html",
    ".htm",
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp"
}

results = []

for restaurant_dir in sorted(DATA_DIR.iterdir()):

    if not restaurant_dir.is_dir():
        continue

    print(f"Processing {restaurant_dir.name}")

    contents = [PROMPT]

    file_count = 0

    for file in sorted(restaurant_dir.iterdir()):

        if file.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        print(f"  Uploading {file.name}")

        try:
            uploaded = client.files.upload(
                file=str(file)
            )

            contents.append(uploaded)
            file_count += 1

        except Exception as ex:
            print(
                f"  Failed uploading "
                f"{file.name}: {ex}"
            )

    if file_count == 0:
        print(
            f"  No supported files found for "
            f"{restaurant_dir.name}"
        )
        continue

    response = None
    chosen_model = None

    for model in MODELS:

        try:
            print(f"  Trying model: {model}")

            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=0
                )
            )

            chosen_model = model

            print(
                f"  Success with {model}"
            )

            break

        except Exception as ex:
            print(
                f"  Model {model} failed:"
            )
            print(f"  {ex}")

    if response is None:
        print(
            f"All models failed for "
            f"{restaurant_dir.name}"
        )
        continue

    raw_response = response.text or ""

    debug_file = (
        restaurant_dir
        / "gemini_response.txt"
    )

    debug_file.write_text(
        raw_response,
        encoding="utf-8"
    )

    text = raw_response.strip()

    if text.startswith("```"):
        lines = text.splitlines()

        if lines:
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines)

    try:
        menu = json.loads(text)

        config = restaurant_config.get(
            restaurant_dir.name,
            {}
        )
        
        final_menu = {
            "name": (
                menu.get("name")
                or config.get("displayName")
                or restaurant_dir.name
            ),
            "lunchMenu": menu.get(
                "lunchMenu",
                []
            ),
            "manual_notes": config.get(
                "manual_notes",
                ""
            )
        }
        
        results.append(final_menu)

        print(
            f"  Parsed menu for "
            f"{restaurant_dir.name}"
        )

    except Exception as ex:

        print(
            f"Failed parsing response for "
            f"{restaurant_dir.name}"
        )

        print(f"Parser error: {ex}")

        print("Raw response follows:")
        print(raw_response)

        error_file = (
            restaurant_dir
            / "parse_error.txt"
        )

        error_file.write_text(
            raw_response,
            encoding="utf-8"
        )

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        results,
        f,
        indent=2,
        ensure_ascii=False
    )

print(
    f"Wrote {OUTPUT_FILE} "
    f"({len(results)} menus)"
)
