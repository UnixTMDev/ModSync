import sys
import requests
from pathlib import Path

print(sys.argv)

file_path = Path(sys.argv[1])
with open(file_path, "rb") as f:
    files = {'file': (file_path.name, f)}  # send only filename, not full path
    res = requests.post("https://mc.unixtm.dev/mods", files=files)

print(res.status_code)
print(res.text)