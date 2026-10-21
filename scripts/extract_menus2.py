import json
import os
import pathlib

from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

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

for restaurant_dir in pathlib.Path("data").iterdir():

    if not restaurant_dir.is_dir():
        continue

    print(f"Processing {restaurant_dir.name}")

    contents = [PROMPT]

    for file in restaurant_dir.iterdir():

        suffix = file.suffix.lower()

        if suffix in [
            ".html",
            ".htm",
            ".pdf",
            ".png",
            ".jpg",
            ".jpeg",
            ".webp"
        ]:

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

with open("menus.json", "w") as f:
    json.dump(
        results,
        f,
        indent=2,
        ensure_ascii=False
    )
