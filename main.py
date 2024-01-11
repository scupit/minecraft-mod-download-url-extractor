import requests
from bs4 import BeautifulSoup

def getModPage(modName: str, versionString: str) -> str:
  return requests.get(f"https://modrinth.com/mod/{modName}/versions", params={
    "g": versionString,
    "l": "fabric"
  }).text

def modDownloadUrl(modName: str, version: str) -> str | None:
  pageHtml = BeautifulSoup(getModPage(modName, version), features="html.parser")
  versionsTable = pageHtml.find(id="all-versions")

  if versionsTable is None:
    return None
  else:
    linkTag = versionsTable.find("a", class_="download-button")
    return linkTag.attrs["href"]

testValid = modDownloadUrl("nvidium", "1.20.3")
testInvalid = modDownloadUrl("nvidium", "1.20.12")

print(testValid)
print(testInvalid)