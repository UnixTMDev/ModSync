import requests
import xml.etree.ElementTree as ET

def get_latest_forge_version():
    url = "https://maven.minecraftforge.net/net/minecraftforge/forge/maven-metadata.xml"
    response = requests.get(url)
    response.raise_for_status()

    root = ET.fromstring(response.content)
    versions = root.find("versioning").find("versions").findall("version")
    version_list = [v.text for v in versions if v.text]

    if not version_list:
        raise ValueError("No Forge versions found.")

    return version_list[0]  # usually the latest version is last

print(get_latest_forge_version())