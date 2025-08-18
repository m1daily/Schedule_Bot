import json
import os
import requests
from dotenv import load_dotenv


load_dotenv()

headers = {"Authorization": f"Bearer {os.environ['GYAZO']}"}
files = {"imagedata": open("image.png", "rb")}
r = requests.post("https://upload.gyazo.com/api/upload", headers=headers, files=files)
try:
    r.raise_for_status()
except requests.RequestException as e:
    print("request failed. error=(%s)", e.response.text)
    exit(1)
url = json.loads(r.text)["url"]

print(url)
