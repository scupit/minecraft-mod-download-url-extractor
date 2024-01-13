import sys
import json
from ModrinthScraper import ItemType, findDownloadUrl
from LinkExtraction import extractLinks, urlToComponents
from ModrinthApi import getMatchingVersions

import logging

logging.basicConfig(level=logging.DEBUG)

# testValid = findDownloadUrl(ItemType.MOD, "nvidium", "1.20.3")
# testInvalid = findDownloadUrl(ItemType.MOD, "nvidium", "1.20.12")
# print(testValid)
# print(testInvalid)

def itemTypeFromString(inType: str) -> ItemType | None:
  match inType:
    case "mod": return ItemType.MOD
    case "plugin": return ItemType.PLUGIN
    case "resourcepack": return ItemType.RESOURCE_PACK
    case "shader": return ItemType.SHADER
    case _: return None

if __name__ == "__main__":
  DESIRED_VERSIONS = ["1.20.1", "1.19.4"]

  if len(sys.argv) < 2:
    print("Missing file path argument.", file=sys.stderr)
    exit(1)

  for link in extractLinks(sys.argv[1]):
    components = urlToComponents(link)
    
    if components is None:
      print("Not a valid URL")
    else:
      itemType = itemTypeFromString(components.paths[0])
      response = getMatchingVersions(components.paths[1], DESIRED_VERSIONS)
      # jsonVersion = json.dumps(response.rawResponse)
      # print(jsonVersion)
      print(response.versions)