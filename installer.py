import json
import time
import traceback
import subprocess,sys,tempfile,webbrowser,requests,os,shutil,platform,tqdm
from InquirerPy import inquirer
MODSYNC_SERVER = "https://mc.unixtm.dev"



CONFIG_EDITS = """
OverrideCommands=true
PreLaunchCommand=LAUNCHCMD
WrapperCommand=
PostExitCommand=
"""
MMC_PACK_DATA_FABRIC = """{
    "components": [
        {
            "cachedName": "LWJGL 3",
            "cachedVersion": "3.3.3",
            "cachedVolatile": true,
            "dependencyOnly": true,
            "uid": "org.lwjgl3",
            "version": "3.3.3"
        },
        {
            "cachedName": "Minecraft",
            "cachedRequires": [
                {
                    "suggests": "3.3.3",
                    "uid": "org.lwjgl3"
                }
            ],
            "cachedVersion": "MINECRAFTVERSION",
            "important": true,
            "uid": "net.minecraft",
            "version": "MINECRAFTVERSION"
        },
        {
            "cachedName": "Intermediary Mappings",
            "cachedRequires": [
                {
                    "equals": "MINECRAFTVERSION",
                    "uid": "net.minecraft"
                }
            ],
            "cachedVersion": "MINECRAFTVERSION",
            "cachedVolatile": true,
            "dependencyOnly": true,
            "uid": "net.fabricmc.intermediary",
            "version": "MINECRAFTVERSION"
        },
        {
            "cachedName": "Fabric Loader",
            "cachedRequires": [
                {
                    "uid": "net.fabricmc.intermediary"
                }
            ],
            "cachedVersion": "LOADERVERSION",
            "uid": "net.fabricmc.fabric-loader",
            "version": "LOADERVERSION"
        }
    ],
    "formatVersion": 1
}
"""
MMC_PACK_DATA_FORGE = """{
    "components": [
        {
            "cachedName": "LWJGL 3",
            "cachedVersion": "3.2.2",
            "cachedVolatile": true,
            "dependencyOnly": true,
            "uid": "org.lwjgl3",
            "version": "3.2.2"
        },
        {
            "cachedName": "Minecraft",
            "cachedRequires": [
                {
                    "suggests": "3.2.2",
                    "uid": "org.lwjgl3"
                }
            ],
            "cachedVersion": "MINECRAFTVERSION",
            "important": true,
            "uid": "net.minecraft",
            "version": "MINECRAFTVERSION"
        },
        {
            "cachedName": "Forge",
            "cachedRequires": [
                {
                    "equals": "MINECRAFTVERSION",
                    "uid": "net.minecraft"
                }
            ],
            "cachedVersion": "LOADERVERSION",
            "uid": "net.minecraftforge",
            "version": "LOADERVERSION"
        }
    ],
    "formatVersion": 1
}
"""
DEFAULT_PRISM_CONFIG = """[General]
ConfigVersion=1.2
iconKey=default
name=INSTANCENAME
InstanceType=OneSix"""
# ^ This is so awful, but this all needs to be in the same EXE file. :(

launchcommands = {}
installers = {}
def undefined_os(asdf=False):
    print(f"This OS ({platform.system()}) is not currently supported.\nYou may request an OS to be added by DMing @UnixTMDev on Discord.")

def downloadFile(url, path):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()  # blow up early if it died
        total_size = int(r.headers.get('content-length', 0))
        block_size = 8192  # 8 KiB chunks
        with open(path, 'wb') as f, tqdm.tqdm(
            total=total_size, unit='iB', unit_scale=True, unit_divisor=1024
        ) as bar:
            for chunk in r.iter_content(chunk_size=block_size):
                if chunk:  # filter out keep-alive chunks
                    f.write(chunk)
                    bar.update(len(chunk))
def downloadURL(url, f):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()  # blow up early if it died
        total_size = int(r.headers.get('content-length', 0))
        block_size = 8192  # 8 KiB chunks
        with tqdm.tqdm(
            total=total_size, unit='iB', unit_scale=True, unit_divisor=1024
        ) as bar:
            for chunk in r.iter_content(chunk_size=block_size):
                if chunk:  # filter out keep-alive chunks
                    f.write(chunk)
                    bar.update(len(chunk))


import re

def clean(s):
    # Replace fancy quotes and normalize
    s = s.replace('"', '\'').replace("'", "-")
    
    # Replace multiple punctuation with a single one, or strip it
    s = re.sub(r'[.,!?;:]+', '', s)  # kill trailing punctuation
    s = re.sub(r'\s*[-–—]+\s*', ' ', s)  # normalize dashes to space
    
    # Remove any characters not allowed in folder names (Windows-safe)
    s = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '', s)
    
    # Replace multiple spaces with one
    s = re.sub(r'\s+', ' ', s).strip()

    return s

def getServerList():
    try:
        res = requests.get("https://mc.unixtm.dev/srvlist").text
        return json.loads(res) # This should always be an array. That IS how the API works.
    except Exception as e:
        print("Error getting server list:",e)

def get_latest_loader_version(loader, retries=6, delay=1):
    if loader != "fabric":
        raise ValueError("Only Fabric is supported for now.")

    url = "https://meta.fabricmc.net/v2/versions/loader"

    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url)
            response.raise_for_status()
            loader_data = response.json()

            if not loader_data:
                raise ValueError("Received empty loader data.")

            # Attempt to get the loader version
            version = loader_data[0]["version"]
            #print(f"Successfully got loader version: {version}")
            return version

        except (KeyError, IndexError, requests.RequestException, ValueError) as e:
            print(f"[Attempt {attempt}/{retries}] Error fetching loader version: {e}")
            if attempt < retries:
                time.sleep(delay)
            else:
                raise RuntimeError("Exceeded max retries while fetching Fabric loader version.")

#Placeholders:
#LAUNCHCMD == PreLaunchCommand
#MINECRAFTVERSION
#LOADERVERSION == Mod loader version
#INSTANCENAME
def install_windows(adding=False):
    def GetLaunchCommand(appdata):
        import os
        relative_path = "MinecraftModSync\\client.exe"
        full_path = os.path.join(appdata, relative_path)
        # Escape backslashes
        escaped_path = full_path.replace("\\", "\\\\")
        # Add escaped quotes
        return f'\\"{escaped_path}\\"'

    try:
        appdata = os.getenv('APPDATA')
        prismPath = os.path.join(appdata,"PrismLauncher")
        installPath = os.path.join(appdata,"MinecraftModSync")
        if not adding:
            os.makedirs(installPath,exist_ok=True)

            downloadFile(f"https://unixtm.dev/modsync/client.exe",os.path.join(installPath,"client.exe"))
        server_names = getServerList()
        choices = []
        instances = os.listdir(os.path.join(prismPath,"instances"))
        for x in server_names:
            if x not in instances:
                choices.append({"value":x,"name":x.title()})
        choices.append({"value":exit, "name": "Cancel"})
        if len(choices) == 1: # Only `exit` is in list
            print("All available server instances are installed. There are no servers left to install.")
            return
        choice = menu("What server do you want an instance for?",choices,choices[0])
        if choice == exit:
            print("Okay. Goodbye!")
            return
        serverInfo = requests.get(f"https://mc.unixtm.dev/info/{choice}").json()
        instancePath = os.path.join(prismPath,"instances",choice)
        try:
            os.makedirs(instancePath)
        except FileExistsError:
            shutil.rmtree(instancePath)
            os.makedirs(instancePath,exist_ok=True)

        instanceConfig = DEFAULT_PRISM_CONFIG+"\n"+CONFIG_EDITS
        instanceConfig = instanceConfig.replace("INSTANCENAME",f"ModSync: {choice}").replace("LAUNCHCMD",GetLaunchCommand(appdata))
        with open(os.path.join(instancePath,"instance.cfg"),"w") as f:
            f.write(instanceConfig)
        instancePack = (MMC_PACK_DATA_FABRIC if serverInfo.get("loader","fabric") == "fabric" else MMC_PACK_DATA_FORGE).replace("MINECRAFTVERSION",serverInfo.get("minecraftVersion", "1.18.2")).replace("LOADERVERSION",get_latest_loader_version(serverInfo.get("loader","fabric")))
        with open(os.path.join(instancePath,"mmc-pack.json"),"w") as f:
            f.write(instancePack)
        print(f"ModSync should now be installed! Open Prism Launcher (relaunch if already open), and select the instance named \"ModSync: {choice}\"")
    except Exception as e:
        print("An error has occured:",traceback.format_exc(e))
installers["Windows"] = install_windows

launchcommands["Windows"] = "MinecraftModSync\\\\client.exe"

def latestPrismLauncherURL(ext):
    import requests

    # GitHub API URL for latest release
    api_url = "https://api.github.com/repos/PrismLauncher/PrismLauncher/releases/latest"

    # Get the latest release info
    resp = requests.get(api_url)
    resp.raise_for_status()
    release = resp.json()

    # Find the Windows .exe asset
    for asset in release["assets"]:
        name = asset["name"].lower()
        if name.endswith(f".{ext}") and "portable" not in name:
            return asset["browser_download_url"]
            break
    else:
        raise Exception(f"Prism Launcher file with extension {ext} not found.")

def ensurePrismLauncherInstalled():
    if platform.system() == "Windows":
        appdata = os.getenv('APPDATA')
        installPath = os.path.join(appdata,"MinecraftModSync")
        os.makedirs(installPath,exist_ok=True)
        PrismLauncherInstalled = os.path.exists(appdata+"\\PrismLauncher")
        if not PrismLauncherInstalled:
            print("You do not have Prism Launcher installed. However, because you are on Windows, this program can automatically download and start the Prism Launcher installer.")
            answer = input("Would you like to do so? (Y/n) ").lower().strip()
            if not answer or answer == "y": #Affirmative
                tmpPath = os.path.join(installPath,"prism_installer.exe")
                tmp = open(tmpPath,"w+b")
                downloadURL(latestPrismLauncherURL("exe"),tmp)
                tmp.close()
                print("Running Prism Launcher installer...")
                subprocess.run([tmpPath])
                appdata = os.getenv('APPDATA')
                time.sleep(1)
                PrismLauncherInstalled = os.path.exists(appdata+"\\PrismLauncher")
                if not PrismLauncherInstalled:
                    raise Exception("Prism Launcher was not installed after running the installer. This should never happen.")
                else:
                    print("Prism Launcher successfully installed!")
                    return
            else:
                print("MinecraftModSync cannot function without features Prism Launcher has that the official launcher does not.")
                input("Press Enter to exit...")
                sys.exit(0)
                print("Exit failed?")
                return
        else:
            print("Prism Launcher is already installed!\nContinuing with installation...")
            return
    else:
        print("Your OS does not support auto-downloading Prism Launcher. You can find the installers at https://prismlauncher.org/download")
        answer = input("Would you like to open that page in your web browser? (Y/n) ").lower().strip()
        if not answer or answer == "y": #Affirmative
            webbrowser.open_new("https://prismlauncher.org/download?from=button")
        input("Press Enter to continue once Prism Launcher is installed. Make sure it isn't open.")
        return


def ensureModSyncInstalled():
    if platform.system() == "Windows":
        appdata = os.getenv('APPDATA')
        installPath = os.path.join(appdata,"MinecraftModSync")
        if not os.path.exists(installPath):
            raise Exception("You do not have ModSync installed. Restart the installer and select Install.")


def menu(msg,choices,default):
    choice = inquirer.select(
        message=msg,
        choices=choices,
        default=default or choices[0],  # optional
    ).execute()

    return choice

# Example usage
if __name__ == "__main__":
    choices = [
            {"name": "Install", "value": "install"},
            {"name": "Add New Instance", "value": "new"},
            {"name": "Exit", "value": "exit"},
        ]
    choice = menu("What would you like to do? (up/enter/down to navigate)",choices,"install")
    if choice == "install":
        ensurePrismLauncherInstalled()
        installers.get(platform.system(),undefined_os)() # Call the function stored in installers under the current OS, and call undefined_os() if not found.
    elif choice == "new":
        ensureModSyncInstalled()
        installers.get(platform.system(),undefined_os)(True)
    elif choice == "exit":
        sys.exit(0)
    input("Press Enter to exit...")