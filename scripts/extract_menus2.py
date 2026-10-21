import json
import os
from pathlib import Path

from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

DATA_DIR = REPO_ROOT / "data"
OUTPUT_FILE = REPO_ROOT / "menus.json"

if not DATA_DIR.exists():
    raise RuntimeError(
        f"Data directory not found: {DATA_DIR}"
    )

PROMPT = """
Extract the lunch menu.

Use ALL provided files:
- HTML
- PDFs
- Images

Return ONLY valid JSON:

{
  "restaurant": "",
  "days": [
    {
      "date": "",
      "meals": []
    }
  ]
}

If no menu is found, return:

{
  "restaurant": "",
  "days": []
}
"""

results = []

for restaurant_dir in DATA_DIR.iterdir():

    if not restaurant_dir.is_dir():
        continue

    print(f"Processing {restaurant_dir.name}")

    contents = [PROMPT]

    for file in restaurant_dir.iterdir():

        suffix = file.suffix.lower()

        if suffix in {
            ".html",
            ".htm",
            ".pdf",
            ".png",
            ".jpg",
            ".jpeg",
            ".webp"
        }:

            uploaded = client.files.upload(
                file=str(file)
            )

            contents.append(uploaded)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=types.GenerateContentConfig(
            temperature=0
        )
    )

    try:
        menu = json.loads(response.text)
        results.append(menu)

    except Exception:
        print(
            f"Failed parsing response for "
            f"{restaurant_dir.name}"
        )

        print(response.text)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(
        results,
        f,
        indent=2,
        ensure_ascii=False
    )
