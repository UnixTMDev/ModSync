import sys
import requests
from pathlib import Path
import os
import json

#GET /mods returns JSON list
#TEST COMMENT, IF I SEE THIS THEN UPDATER WORKED
#GET /mod/<file> sends back file

#print(sys.argv)

res = requests.get("https://mc.unixtm.dev/mods")

#print(res.status_code)
#print(res.text)

mods = json.loads(res.text)

modsDir = ""

if os.environ.get("INST_MC_DIR",None) != None:
    modsDir = Path(os.environ.get("INST_MC_DIR")+"\\mods\\")
elif len(sys.argv) > 1:
    modsDir = Path(sys.argv[1])
else:
    print("This script has been called without a directory. This should never happen.")
    sys.exit(1)

location = modsDir.absolute().as_posix()
installed = os.listdir(location)

for x in mods:
    if x not in installed:
        res2 = requests.get("https://mc.unixtm.dev/mod/"+x)
        res2.raise_for_status()
        with open(location+"/"+x,"wb") as f:
            f.write(res2.content)
