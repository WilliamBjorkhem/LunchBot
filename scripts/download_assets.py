import json
import pathlib
import requests

for assets_file in pathlib.Path("data").glob("*/assets.json"):
    folder = assets_file.parent

    assets = json.loads(assets_file.read_text())

    for idx, url in enumerate(assets):
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()

            suffix = pathlib.Path(url).suffix
            if not suffix:
                suffix = ".bin"

            (folder / f"asset_{idx}{suffix}").write_bytes(r.content)

        except Exception as e:
            print(e)
