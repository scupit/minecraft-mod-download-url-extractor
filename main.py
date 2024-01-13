import asyncio
import aiohttp
import sys
import json
from ItemType import ItemType
from ModrinthScraper import findDownloadUrl
from LinkExtraction import extractLinks, urlToComponents, UrlComponents
from ModrinthApi import ProjectVersion, ModrinthApi

import logging

# logging.basicConfig(level=logging.DEBUG)

# testValid = findDownloadUrl(ItemType.MOD, "nvidium", "1.20.3")
# testInvalid = findDownloadUrl(ItemType.MOD, "nvidium", "1.20.12")
# print(testValid)
# print(testInvalid)

DESIRED_VERSIONS = ["1.20.1", "1.19.4"]

def itemTypeFromString(inType: str) -> ItemType | None:
  match inType:
    case "mod":           return ItemType.MOD
    case "plugin":        return ItemType.PLUGIN
    case "resourcepack":  return ItemType.RESOURCE_PACK
    case "shader":        return ItemType.SHADER
    case "datapack":      return ItemType.DATA_PACK
    case _:               return None

def findMostRecentMatching(versionString: str, versionList: list[ProjectVersion]) -> ProjectVersion | None:
  matching = list(filter(
    lambda pv : versionString in pv.supportedVersions,
    versionList
  ))
  matching.sort(key=lambda pv : pv.datePublished)

  return matching[-1] if len(matching) > 0 else None

async def printInfoFromComponents(api: ModrinthApi, components: UrlComponents):
  itemType = itemTypeFromString(components.paths[0])

  if itemType is None:
    print(f"Unable to determine item type using string \"{components.paths[0]}\"")
    return

  projectName = components.paths[1]
  checkingVersion = DESIRED_VERSIONS[0]
  versions = await api.getMatchingVersions(itemType, projectName, DESIRED_VERSIONS)
  bestMatch = findMostRecentMatching(checkingVersion, versions)

  if bestMatch == None:
    print(f"No match for {projectName} - {checkingVersion}", file=sys.stderr)
  else:
    print(bestMatch.primaryFile().url)

async def main():
  if len(sys.argv) < 2:
    print("Missing file path argument.", file=sys.stderr)
    exit(1)
  
  async with aiohttp.ClientSession() as session:
    api = ModrinthApi(session)
    results = []

    for link in extractLinks(sys.argv[1]):
      components = urlToComponents(link)

      if components is None:
        print("Not a valid URL", file=sys.stderr)
      elif components.domain != "modrinth.com":
        print("Not a Modrinth URL", file=sys.stderr)
      else:
        results.append(printInfoFromComponents(api, components))
    
    results = await asyncio.gather(*results)

if __name__ == "__main__":
  asyncio.run(main())