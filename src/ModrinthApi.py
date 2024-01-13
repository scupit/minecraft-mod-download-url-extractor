from aiohttp import ClientSession
from dataclasses import dataclass
from datetime import datetime
from typing import Any, assert_never
from ItemType import ItemType

MODRINTH_API_BASE: str = "https://api.modrinth.com/v2"

@dataclass
class HashGroup:
  sha1: str
  sha512: str

@dataclass
class ProjectFile:
  hashes: HashGroup
  url: str
  fileName: str
  isPrimary: bool

def _projectFileFromJson(fileJson) -> ProjectFile:
  return ProjectFile(
    hashes=HashGroup(
      sha1=fileJson["hashes"]["sha1"],
      sha512=fileJson["hashes"]["sha512"]
    ),
    url=fileJson["url"],
    fileName=fileJson["filename"],
    isPrimary=fileJson["primary"]
  )

@dataclass
class DependencyDescription:
  versionId: str
  projectId: str
  isRequired: bool

def _dependencyFromJson(depJson) -> DependencyDescription:
  return DependencyDescription(
    versionId=depJson["version_id"],
    projectId=depJson["project_id"],
    isRequired= depJson["dependency_type"] == "required"
  )

@dataclass
class ProjectVersion:
  # Not the semver number. versionId is a seemingly random string.
  versionId: str
  projectId: str
  datePublished: datetime
  supportedVersions: list[str]
  files: list[ProjectFile]
  # These are currently "raw" dependencies. They haven't been resolved yet.
  dependencies: list[DependencyDescription]

  def primaryFile(self) -> ProjectFile:
    for file in self.files:
      if file.isPrimary:
        return file
    assert False, "unreachable"

def _projectVersionFromJson(versionJson) -> ProjectVersion:
  return ProjectVersion(
    versionId=versionJson["id"],
    projectId=versionJson["project_id"],
    datePublished=datetime.fromisoformat(versionJson["date_published"]),
    supportedVersions=versionJson["game_versions"],
    files=[_projectFileFromJson(fileJson) for fileJson in versionJson["files"]],
    dependencies=[_dependencyFromJson(depJson) for depJson in versionJson["dependencies"]]
  )

def queryList(itemList: list[str]) -> str:
  quotedItems = map(
    lambda s : f"\"{s}\"",
    itemList
  )
  joined = ",".join(quotedItems)
  return f"[{joined}]"

def _isListed(versionJson) -> bool:
  return versionJson["status"] == "listed"

def getLoaderNameForItemType(itemType: ItemType) -> str | None:
  match itemType:
    case ItemType.MOD | ItemType.PLUGIN:  return "fabric"
    case ItemType.SHADER:                 return "iris"
    case ItemType.RESOURCE_PACK:          return None
    case ItemType.DATA_PACK:              return "datapack"

class ModrinthApi:
  _httpSession: ClientSession

  def __init__(self, session: ClientSession):
    self._httpSession = session

  async def _getJson(self, url: str, params: dict[str, str]) -> Any:
    response = await self._httpSession.get(url, params=params)
    return await response.json()
  
  async def getMatchingVersions(
    self,
    itemType: ItemType,
    projectName: str,
    desiredVersions: list[str]
  ) -> list[ProjectVersion]:
    url = f"{MODRINTH_API_BASE}/project/{projectName}/version"
    params = {
      "game_versions": queryList(desiredVersions)
    }

    loader = getLoaderNameForItemType(itemType)
    if loader is not None:
      params["loaders"] = queryList([loader])

    # https://docs.modrinth.com/api-spec#tag/versions/operation/getProjectVersions
    response = list(filter(
      _isListed,
      await self._getJson(url, params)
    ))

    return [_projectVersionFromJson(versionJson) for versionJson in response]

  async def resolveDependency(self, depDescription: DependencyDescription) -> ProjectVersion:
    url = f"{MODRINTH_API_BASE}/project/{depDescription.projectId}/version/{depDescription.versionId}"
    return _projectVersionFromJson(await self._getJson(url, {}))