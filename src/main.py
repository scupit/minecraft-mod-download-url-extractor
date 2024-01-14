import asyncio
import aiohttp
import sys
import json
from enum import Enum
from dataclasses import dataclass

from ItemType import ItemType
from typing import Any, Coroutine
from CurseForgeScraper import CurseForgeScraper
from LinkExtraction import extractLinks, urlToComponents, UrlComponents
from ModrinthApi import ProjectVersion, ModrinthApi
from Helpers import printStderr
from playwright.async_api import async_playwright, Browser

import logging

logging.basicConfig(level=logging.DEBUG)

# testValid = findDownloadUrl(ItemType.MOD, "nvidium", "1.20.3")
# testInvalid = findDownloadUrl(ItemType.MOD, "nvidium", "1.20.12")
# print(testValid)
# print(testInvalid)

class MatchResultType(Enum):
  UNKNOWN_PROJECT_TYPE = 1
  NO_MATCH = 2
  MATCH_FOUND = 3

@dataclass
class MatchSearchResult:
  resultType: MatchResultType
  message: str

def findMostRecentMatching(versionString: str, versionList: list[ProjectVersion]) -> ProjectVersion | None:
  matching = list(filter(
    lambda pv : versionString in pv.supportedVersions,
    versionList
  ))
  matching.sort(key=lambda pv : pv.datePublished)

  return matching[-1] if len(matching) > 0 else None

async def getModrinthInfoFromComponents(
  api: ModrinthApi,
  components: UrlComponents,
  versionSearching: str
) -> MatchSearchResult:
  itemType = ModrinthApi.itemTypeFromString(components.paths[0])

  if itemType is None:
    return MatchSearchResult(
      MatchResultType.UNKNOWN_PROJECT_TYPE,
      components.wholeUrl()
    )

  projectName = components.paths[1]
  versions = await api.getMatchingVersions(itemType, projectName, [versionSearching])
  bestMatch = findMostRecentMatching(versionSearching, versions)

  if bestMatch == None:
    return MatchSearchResult(
      MatchResultType.NO_MATCH,
      f"No match for {projectName} - {versionSearching}"
    )
  else:
    return MatchSearchResult(
      MatchResultType.MATCH_FOUND,
      bestMatch.primaryFile().url
    )

async def resolveCurseForgeResults(coroutineList: list) -> list[str]:
  results: list[str] = []
  for coro in coroutineList:
    results.append(await coro)
    await asyncio.sleep(CurseForgeScraper.CRAWL_DELAY.seconds)
  return results

async def setup():
  async with async_playwright() as playwright:
    browser = await playwright.firefox.launch()
    async with aiohttp.ClientSession() as session:
      await main(browser, session)
    await browser.close()

async def main(browser: Browser, session: aiohttp.ClientSession):
  # DESIRED_VERSIONS = ["1.20.1", "1.19.4"]
  VERSION_SEARCHING: str = "1.20.1"

  if len(sys.argv) < 2:
    printStderr("Missing file path argument.")
    exit(1)
  
  modrinthApi = ModrinthApi(session)
  curseForgeScraper = CurseForgeScraper(browser)
  
  maybeInvalid: list[str] = [ ]
  needsManualDownload: list[str] = [ ]
  pendingModrinthResults: list[Coroutine[Any, Any, MatchSearchResult]] = [ ]
  pendingCurseForgeResults = [ ]

  for link in extractLinks(sys.argv[1]):
    components = urlToComponents(link)

    if components is None:
      printStderr(f"Invalid URL: \"{link}\"")
      continue

    match components.domain:
      case "modrinth.com":
        pendingModrinthResults.append(getModrinthInfoFromComponents(modrinthApi, components, VERSION_SEARCHING))
      case "www.curseforge.com":
        itemType = CurseForgeScraper.itemTypeFromString(components.paths[1])

        if itemType is None:
          maybeInvalid.append(link)
        elif not CurseForgeScraper.isItemTypeSupported(itemType):
          needsManualDownload.append(link)
        else:
          projectName = components.paths[2]
          pendingCurseForgeResults.append(curseForgeScraper.getLinkFor(itemType, projectName, VERSION_SEARCHING))

  printStderr("Gathering Download URLs...")

  modrinthResults: list[MatchSearchResult]
  curseForgeResults: list[str]

  modrinthResults, curseForgeResults = await asyncio.gather(
    asyncio.gather(*pendingModrinthResults),
    resolveCurseForgeResults(pendingCurseForgeResults)
  )

  for result in modrinthResults:
    match result.resultType:
      case MatchResultType.UNKNOWN_PROJECT_TYPE:
        printStderr(f"Invalid project type for URL \"{result.message}\"")
      case MatchResultType.NO_MATCH:
        print(result.message)
      case MatchResultType.MATCH_FOUND:
        print(result.message)

  for result in curseForgeResults:
    print(result)
  
  for result in needsManualDownload:
    print(result)
  
  for result in maybeInvalid:
    printStderr(f"MAYBE INVALID: {result}")


if __name__ == "__main__":
  asyncio.run(setup())