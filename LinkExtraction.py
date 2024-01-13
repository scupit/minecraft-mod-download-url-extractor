import re
import sys
from typing import cast
from dataclasses import dataclass

markdownLinkRegex = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
httpsRegex = re.compile(r"^(\w+)://([^/]+)(/[^\?]+)?(\?.+)?$")

@dataclass
class UrlComponents:
  protocol: str
  domain: str
  paths: list[str]
  query: dict[str, str]

def onlyNonEmpty(strList: list[str]) -> list[str]:
  result = []
  for string in strList:
    strippedStr = string.strip()
    if len(strippedStr) > 0:
      result.append(strippedStr)
  return result

def getGroupOrEmpty(regexMatch: re.Match[str], index: int) -> str:
  group = regexMatch.group(index)
  return group if group is not None else ""

def urlToComponents(url: str) -> UrlComponents | None:
  regexMatch = httpsRegex.match(url)

  if regexMatch is None:
    return None

  # The [1:] slice removes the leading question mark, if it's there.
  queryPieces = onlyNonEmpty(getGroupOrEmpty(regexMatch, 4)[1:].split("&"))

  return UrlComponents(
    protocol=getGroupOrEmpty(regexMatch, 1),
    domain=getGroupOrEmpty(regexMatch, 2),
    paths=onlyNonEmpty(getGroupOrEmpty(regexMatch, 3).split("/")),
    # For now we'll assume that query strings don't contain extra '='.
    query=dict(entry.split("=") for entry in queryPieces)
  )

def extractMarkdownUrl(line: str) -> str | None:
  regexMatch = markdownLinkRegex.search(line)
  return None if regexMatch is None else regexMatch.group(2)

def extractLinks(relativeFilePath: str) -> list[str]:
  with open(relativeFilePath, "r") as file:
    results = [extractMarkdownUrl(url) for url in file]
    return cast(
      list[str],
      filter(lambda url : url is not None, results)
    )
      
if __name__ == "__main__":
  if len(sys.argv) < 2:
    print("Missing file path argument.", file=sys.stderr)
  else:
    for link in extractLinks(sys.argv[1]):
      components = urlToComponents(link)
      
      if components is None:
        print("Not a valid URL")
      else:
        print(components)