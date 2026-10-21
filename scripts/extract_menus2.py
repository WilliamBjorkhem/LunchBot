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
    "gemini-2.5-flash",
    "gemini-2.5-pro"
]

if not DATA_DIR.exists():
    raise RuntimeError(
        f"Data directory not found: {DATA_DIR}"
    )

PROMPT = """
Extract the lunch menu from all supplied content.

Use ALL provided files:
- HTML
- PDFs
- Images

You must make a best effort to identify:
- restaurant name
- available lunch days
- meal descriptions

Only return an empty days array if you have carefully
examined every supplied file and no menu information exists.

Always populate the restaurant field whenever the name
can be determined from the supplied files.

Return ONLY valid JSON.

Expected format:

{
  "restaurant": "",
  "days": [
    {
      "date": "",
      "meals": []
    }
  ]
}

Do not include markdown.
Do not include explanations.
Do not wrap the JSON in code fences.
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

        menu["_source_directory"] = (
            restaurant_dir.name
        )

        menu["_model"] = chosen_model

        results.append(menu)

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
