import requests,os,shutil,hashlib,platform
sha256 = lambda a: hashlib.sha256(bytes(a,"utf-8")).hexdigest() # Shortcut for a sha256 hash.
def getInstallPath():
    if getattr(sys, 'frozen', False):
        application_path = os.path.abspath(os.path.dirname(sys.executable))
    elif __file__:
        application_path = os.path.abspath(os.path.dirname(__file__))
    return application_path # If this file is ./client.exe or ./client.py, this will be ./
getCorrectSlash = lambda: "\\" if platform.system() == "Windows" else "/" # Because MS had to be the special one.

res = requests.get("https://mc.unixtm.dev/update")
localPath = getInstallPath()+getCorrectSlash()+"check.py" # "~/.MCModSync/check.py" or "%AppData%\MinecraftModSync\check.py"

if os.path.exists(localPath):
    with open(localPath,"r") as f:
        fileContents = f.read()
else:
    fileContents = ""


hashedLatest = sha256(res.text)
hashedLocal = sha256(fileContents)

if hashedLatest != hashedLocal:
    with open(localPath,"w") as f:
        f.write(res.text) #LINE 23

import sys
import requests
from pathlib import Path
import os
import json
# Need to make sure that pyinstaller packages all this
with open(localPath,"r") as f:
    fileContents = f.read()
exec(fileContents)