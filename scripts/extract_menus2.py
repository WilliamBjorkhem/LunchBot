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
