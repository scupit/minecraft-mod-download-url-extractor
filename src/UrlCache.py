from LinkExtraction import UrlComponents

def _urlWithoutQuery(url: UrlComponents) -> str:
  temp = url.query
  result = url.wholeUrl()
  url.query = temp
  return result

class UrlCache:
  _linkSet: set[str]

  def __init__(self):
    self._linkSet = set()
  
  def insert(self, url: UrlComponents):
    self._linkSet.add(_urlWithoutQuery(url))
  
  def hasUrl(self, url: UrlComponents) -> bool:
    return self.hasUrlString(_urlWithoutQuery(url))

  def hasUrlString(self, urlString: str) -> bool:
    return urlString in self._linkSet