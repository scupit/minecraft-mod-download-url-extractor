import argparse
import asyncio
import aiohttp
import sys
import json
from enum import Enum
from dataclasses import dataclass

from ItemType import ItemType
from typing import Any, Coroutine, AsyncGenerator
from CurseForgeScraper import CurseForgeScraper
from LinkExtraction import extractLinks, urlToComponents, UrlComponents
from ModrinthApi import ProjectVersion, ModrinthApi
from Helpers import printStderr
from playwright.async_api import async_playwright, Browser, BrowserContext
from UrlCache import UrlCache

import logging

logging.basicConfig(level=logging.DEBUG)

# testValid = findDownloadUrl(ItemType.MOD, "nvidium", "1.20.3")
# testInvalid = findDownloadUrl(ItemType.MOD, "nvidium", "1.20.12")
# print(testValid)
# print(testInvalid)

@dataclass
class ProgramArgs:
  desiredVersion: str
  fileNameReading: str
  outFileSuffix: str | None

class MatchResultType(Enum):
  UNKNOWN_PROJECT_TYPE = 1
  NO_MATCH = 2
  MATCH_FOUND = 3
  NEEDS_MANUAL_DOWNLOAD = 4

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
  # TODO: Only process if the link wasn't already processed. Need to do that in other places too.
  # if urlCache.hasUrl(components):
  #   return

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
      f"NO MATCH: {projectName} @ {versionSearching}"
    )
  else:
    return MatchSearchResult(
      MatchResultType.MATCH_FOUND,
      bestMatch.primaryFile().url
    )

async def getCurseForgeInfoFromComponents(
  scraper: CurseForgeScraper,
  itemType: ItemType,
  components: UrlComponents,
  versionSearching: str
) -> MatchSearchResult:
  projectName = components.paths[2]
  result: str | None = await scraper.getLinkFor(itemType, projectName, versionSearching)

  if result is None:
    return MatchSearchResult(
      MatchResultType.NEEDS_MANUAL_DOWNLOAD,
      components.wholeUrl()
    )
  
  # NOTE: Some compatibility datapacks (called "texture-packs" in curseforge urls...)
  # are meant for adding compatibility between mods in certain loaders. Those might need
  # manual checking, but for now I don't have a way to determine which packs are configured
  # that way. Those packs are fairly uncommon though, so it shouldn't cause too many issues
  # for now.
  return MatchSearchResult(
    MatchResultType.MATCH_FOUND,
    result
  )

async def resolveCurseForgeResults(coroutineList: list) -> AsyncGenerator[MatchSearchResult, Any]:
  for coro in coroutineList:
    yield await coro
    await asyncio.sleep(CurseForgeScraper.CRAWL_DELAY.seconds)

async def setup(args: ProgramArgs):
  async with async_playwright() as playwright:
    browser = await playwright.firefox.launch()
    context = await browser.new_context(
      viewport={"width": 1920, "height": 1080}
    )

    async with aiohttp.ClientSession() as session:
      await main(context, session, args)
    await browser.close()

async def main(
  browser: BrowserContext,
  session: aiohttp.ClientSession,
  args: ProgramArgs
):
  VERSION_SEARCHING: str = args.desiredVersion

  modrinthApi = ModrinthApi(session)
  curseForgeScraper = CurseForgeScraper(browser)
  urlCache = UrlCache()
  
  maybeInvalid: list[str] = [ ]
  needsManualDownload: list[str] = [ ]
  pendingModrinthResults: list[Coroutine[Any, Any, MatchSearchResult]] = [ ]
  pendingCurseForgeResults: list[Coroutine[Any, Any, MatchSearchResult]] = [ ]

  for link in extractLinks(args.fileNameReading):
    components = urlToComponents(link)

    if components is None:
      printStderr(f"Invalid URL: \"{link}\"")
      continue

    if urlCache.hasUrl(components):
      continue
      
    urlCache.insert(components)

    match components.domain:
      case "modrinth.com":
        pendingModrinthResults.append(getModrinthInfoFromComponents(modrinthApi, components, VERSION_SEARCHING))
      case "www.curseforge.com" | "legacy.curseforge.com":
        itemType = CurseForgeScraper.itemTypeFromString(components.paths[1])

        if itemType is None:
          maybeInvalid.append(link)
        elif not CurseForgeScraper.isItemTypeSupported(itemType):
          needsManualDownload.append(link)
        else:
          pendingCurseForgeResults.append(getCurseForgeInfoFromComponents(curseForgeScraper, itemType, components, VERSION_SEARCHING))

  printStderr("Resolving Modrinth URLs...")
  modrinthResults = await asyncio.gather(*pendingModrinthResults)

  printStderr("Resolving CurseForge URLs...")
  curseForgeResults: list[MatchSearchResult] = []

  counter = 0
  async for result in resolveCurseForgeResults(pendingCurseForgeResults):
    counter += 1
    printStderr(f"Resolved CurseForge URL {counter}/{len(pendingCurseForgeResults)}")
    curseForgeResults.append(result)

  # printStderr("Gathering Download URLs...")
  # modrinthResults: list[MatchSearchResult]
  # curseForgeResults: list[MatchSearchResult]

  # modrinthResults, curseForgeResults = await asyncio.gather(
  #   asyncio.gather(*pendingModrinthResults),
  #   resolveCurseForgeResults(pendingCurseForgeResults)
  # )

  printStderr("--------------------------------------------------------------------------------\n")

  for result in modrinthResults:
    match result.resultType:
      case MatchResultType.UNKNOWN_PROJECT_TYPE:
        printStderr(f"Invalid project type for URL \"{result.message}\"")
      case MatchResultType.NO_MATCH:
        print(result.message)
      case MatchResultType.MATCH_FOUND:
        print(result.message)

  for result in curseForgeResults:
    match result.resultType:
      case MatchResultType.MATCH_FOUND:
        print(result.message)
      case MatchResultType.NEEDS_MANUAL_DOWNLOAD:
        needsManualDownload.append(result.message)
  
  for result in needsManualDownload:
    printStderr(f"NEEDS MANUAL DOWNLOAD: {result}")
  
  for result in maybeInvalid:
    printStderr(f"MAYBE INVALID: {result}")

if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    prog="Mod Download Url Extractor",
    description="Fetches download URLs for minecraft mods, texture packs, etc. given a list of markdown-formatted links."
  )

  parser.add_argument("desired_version")
  parser.add_argument("file_reading")
  parser.add_argument("-o", "--out-name")
  args = parser.parse_args()
  # printStderr(str(args))

  asyncio.run(setup(ProgramArgs(
    desiredVersion=args.desired_version,
    fileNameReading=args.file_reading,
    outFileSuffix=args.out_name
  )))