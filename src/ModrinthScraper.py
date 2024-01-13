#
# NOTE: This file probably isn't needed anymore, but I'll keep it for reference.
#
import requests
from bs4 import BeautifulSoup
from ItemType import ItemType

def modrinthVersionsPage(itemType: str, name: str) -> str:
  return f"https://modrinth.com/{itemType}/{name}/versions"

def getDataPackPage(pluginName: str, versionString: str) -> str:
  return requests.get(modrinthVersionsPage("datapack", pluginName), params={
    "g": versionString,
    "l": "datapack"
  }).text

def getPluginPage(pluginName: str, versionString: str) -> str:
  return requests.get(modrinthVersionsPage("plugin", pluginName), params={
    "g": versionString,
    "l": "fabric"
  }).text

def getShaderPage(shaderName: str, versionString: str) -> str:
  return requests.get(modrinthVersionsPage("shader", shaderName), params={
    "g": versionString,
    "l": "iris"
  }).text

def getResourcePackPage(packName: str, versionString: str) -> str:
  return requests.get(modrinthVersionsPage("resourcepack", packName), params={
    "g": versionString
  }).text

def getModPage(modName: str, versionString: str) -> str:
  return requests.get(modrinthVersionsPage("mod", modName), params={
    "g": versionString,
    "l": "fabric"
  }).text

def pageContents(itemType: ItemType, itemName: str, version: str) -> str:
  match itemType:
    case ItemType.MOD:            return getModPage(itemName, version)
    case ItemType.RESOURCE_PACK:  return getResourcePackPage(itemName, version)
    case ItemType.SHADER:         return getShaderPage(itemName, version)
    case ItemType.PLUGIN:         return getPluginPage(itemName, version)
    case ItemType.DATA_PACK:      return getDataPackPage(itemName, version)

def findDownloadUrl(itemType: ItemType, modName: str, version: str) -> str | None:
  pageHtml = BeautifulSoup(pageContents(itemType, modName, version), features="html.parser")
  versionsTable = pageHtml.find(id="all-versions")

  if versionsTable is None:
    return None
  else:
    linkTag = versionsTable.find("a", class_="download-button")
    return linkTag.attrs["href"]
