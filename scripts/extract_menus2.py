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

RESTAURANTS_FILE = (
    SCRIPT_DIR / "restaurants.json"
)

MODELS = [
    "gemini-3.8-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite"
]

if not DATA_DIR.exists():
    raise RuntimeError(
        f"Data directory not found: {DATA_DIR}"
    )

restaurant_config = {
    entry["name"]: entry
    for entry in json.loads(
        RESTAURANTS_FILE.read_text(
            encoding="utf-8"
        )
    )
}

PROMPT = """
Extract today's lunch menu.

Use ALL supplied files:
- HTML
- Images
- PDFs

Return ONLY valid JSON.

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
- name = restaurant name
- lunchMenu contains every lunch dish found
- description may be empty
- do not return markdown
- do not return explanations
- do not return code fences
- if no menu can be found use an empty lunchMenu array
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


def clean_response(text):
    text = text.strip()

    if text.startswith("```"):
        lines = text.splitlines()

        if len(lines) > 1:
            lines = lines[1:]

        if (
            lines and
            lines[-1].strip() == "```"
        ):
            lines = lines[:-1]

        text = "\n".join(lines)

    first = text.find("{")
    last = text.rfind("}")

    if first >= 0 and last > first:
        text = text[first:last + 1]

    return text


for restaurant_dir in sorted(DATA_DIR.iterdir()):

    if not restaurant_dir.is_dir():
        continue

    print(
        f"Processing {restaurant_dir.name}"
    )

    contents = [PROMPT]

    file_count = 0

    for file in sorted(
        restaurant_dir.iterdir()
    ):

        if (
            file.suffix.lower()
            not in SUPPORTED_EXTENSIONS
        ):
            continue

        print(
            f"  Uploading {file.name}"
        )

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
            f"  No supported files "
            f"found for "
            f"{restaurant_dir.name}"
        )
        continue

    response = None
    chosen_model = None

    for model in MODELS:

        try:
            print(
                f"  Trying model: "
                f"{model}"
            )

            response = (
                client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        temperature=0
                    )
                )
            )

            chosen_model = model

            print(
                f"  Success with "
                f"{model}"
            )

            break

        except Exception as ex:
            print(
                f"  Model {model} "
                f"failed:"
            )

            print(ex)

    if response is None:
        print(
            f"All models failed for "
            f"{restaurant_dir.name}"
        )
        continue

    raw_response = (
        response.text or ""
    )

    (
        restaurant_dir /
        "gemini_response.txt"
    ).write_text(
        raw_response,
        encoding="utf-8"
    )

    try:

        menu = json.loads(
            clean_response(
                raw_response
            )
        )

        config = restaurant_config.get(
            restaurant_dir.name,
            {}
        )

        final_menu = {
            "name":
                menu.get("name")
                or config.get(
                    "displayName"
                )
                or restaurant_dir.name,

            "lunchMenu":
                menu.get(
                    "lunchMenu",
                    []
                ),

            "manual_notes":
                config.get(
                    "manual_notes",
                    ""
                )
        }

        results.append(
            final_menu
        )

        print(
            f"  Parsed menu for "
            f"{restaurant_dir.name}"
        )

    except Exception as ex:

        print(
            f"Failed parsing "
            f"{restaurant_dir.name}"
        )

        print(ex)

        (
            restaurant_dir /
            "parse_error.txt"
        ).write_text(
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
