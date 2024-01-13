import requests
from dataclasses import dataclass
from datetime import datetime
from typing import Any

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
class Dependency:
  versionId: str
  projectId: str
  isRequired: bool

def _dependencyFromJson(depJson) -> Dependency:
  return Dependency(
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
  dependencies: list[Dependency]

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

@dataclass
class VersionsResponse:
  rawResponse: Any
  versions: list[ProjectVersion]

def getMatchingVersions(projectName: str, desiredVersions: list[str]) -> VersionsResponse:
  url = f"{MODRINTH_API_BASE}/project/{projectName}/version"

  # https://docs.modrinth.com/api-spec#tag/versions/operation/getProjectVersions
  response = list(filter(
    _isListed,
    requests.get(url, params={
      "loaders": queryList(["fabric"]),
      "game_versions": queryList(desiredVersions)
    }).json()
  ))

  return VersionsResponse(
    rawResponse=response,
    versions=[_projectVersionFromJson(versionJson) for versionJson in response]
  )