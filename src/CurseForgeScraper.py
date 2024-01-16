import asyncio
from aiohttp import ClientSession
from ItemType import ItemType
from LinkExtraction import UrlComponents, urlToComponents
from playwright.async_api import BrowserContext
from datetime import timedelta
from bs4 import BeautifulSoup, Tag

CURSE_FORGE_BASE_URL: str = "https://www.curseforge.com/minecraft"

def _curseForgeVersionsPage(itemType: str, name: str) -> str:
  return f"{CURSE_FORGE_BASE_URL}/{itemType}/{name}/files"

class CurseForgeScraper:
  # Crawl delay specified here: https://curseforge.com/robots.txt
  CRAWL_DELAY = timedelta(seconds=1)
  _browser: BrowserContext

  def __init__(self, browser: BrowserContext):
    self._browser = browser

  async def _requestPageHtml(self, url: str, params: dict[str, str]) -> str:
    components = urlToComponents(url)
    assert components is not None
    components.query = params
    # print(f"Scraping page at {components.wholeUrl()}")

    page = await self._browser.new_page()
    await page.goto(components.wholeUrl(), wait_until="load")

    # This is a hack. The table takes an extra bit of time to populate.
    # For consistency, it might be worth figuring out a better way to do this.
    await asyncio.sleep(1)
    responseText = await page.content()
    await page.close()

    return responseText

  @staticmethod
  def itemTypeFromString(inType: str) -> ItemType | None:
    match inType:
      case "mc-mods":         return ItemType.MOD
      case "texture-packs":   return ItemType.RESOURCE_PACK
      case _:                 return None

  @staticmethod
  def isItemTypeSupported(itemType: ItemType) -> bool:
    return itemType == ItemType.RESOURCE_PACK

  async def _getResourcePackPage(self, packName: str, versionString: str) -> str:
    url = _curseForgeVersionsPage("texture-packs", packName)
    return await self._requestPageHtml(url, params={
      "version": versionString
    })

  async def _getPageForItem(self, itemType: ItemType, projectName: str, versionString: str) -> str | None:

    match itemType:
      case ItemType.RESOURCE_PACK: return await self._getResourcePackPage(projectName, versionString)
      case _: return None

  async def getLinkFor(
    self,
    itemType: ItemType,
    projectName: str,
    desiredVersion: str
  ) -> str | None:
    page = await self._getPageForItem(itemType, projectName, desiredVersion)

    if page is None:
      return None

    # with open(f"test-files/{projectName}.html", "w") as html:
    #   html.write(page)
    
    page = BeautifulSoup(page, features="html.parser")
    candidates = page.find_all("a", class_="file-row")
    # print(len(candidates), flush=True)

    for linkElement in candidates:
      versionList: list[Tag] = linkElement.css.select(".tooltip > ul > li")
      for tag in versionList:
        if tag.text == desiredVersion:
          match linkElement.get("href"):
            # downloadLink is the absolute path to the file in curseforge.com.
            # It contains a leading slash, but doesn't contain the domain name.
            case str(downloadLink): return f"https://www.curseforge.com{downloadLink}"
            case _: continue
    
    return None
