import os
import requests
from pathlib import Path
import sys

API_BASE = "https://mc.unixtm.dev"

def get_env_or_input(var_name, prompt):
    value = os.getenv(var_name)
    if not value:
        value = input(f"{prompt}: ").strip()
    return value

def flatten_file_tree(tree, path=""):
    """Flatten the nested JSON file tree into a dict of rel_path -> download_url"""
    files = {}
    for name, content in tree.items():
        current_path = f"{path}/{name}" if path else name
        if isinstance(content, dict):
            files.update(flatten_file_tree(content, current_path))
        else:
            files[current_path] = content
    return files

def download_file(url, dest):
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(url, stream=True)
        if r.status_code == 200:
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"[+] Downloaded {dest}")
        else:
            print(f"[!] Failed to download {url} - status {r.status_code}")
    except Exception as e:
        print(f"[!] Error downloading {url}: {e}")

def sync_server_files():
    inst_id = get_env_or_input("INST_ID", "Enter instance ID (server name)")
    inst_mc_dir = Path(get_env_or_input("INST_MC_DIR", "Enter instance Minecraft directory")).resolve()

    print(f"[*] Using INST_ID = {inst_id}")
    print(f"[*] Using INST_MC_DIR = {inst_mc_dir}")

    list_url = f"{API_BASE}/list/{inst_id}"
    print(f"[*] Fetching file list from {list_url}")
    r = requests.get(list_url)
    if r.status_code != 200:
        print(f"[!] Failed to fetch file list for server '{inst_id}': {r.status_code}")
        sys.exit(1)

    file_tree = r.json()
    files = flatten_file_tree(file_tree)

    print(f"[*] Found {len(files)} files to check.")
    for rel_path, download_url in files.items():
        local_path = inst_mc_dir / rel_path
        if not local_path.exists():
            print(f"[-] Missing: {rel_path}")
            download_file(f"{API_BASE}{download_url}", local_path)
        else:
            # Uncomment to log already-present files
            # print(f"[=] Exists: {rel_path}")
            pass

    print("[OK] Sync complete.")

if __name__ == "__main__":
    sync_server_files()

