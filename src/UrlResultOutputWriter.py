# from io import TextIOWrapper, TextIOBase
from typing import TextIO
import sys

class UrlResultOutputWriter:
  _successFileOut: TextIO | None = None
  _failFileOut: TextIO | None = None

  def __init__(self, fileOutputPath: str | None = None):
    if fileOutputPath is not None:
      self._successFileOut = open(f"{fileOutputPath}-success.txt", "w")
      self._failFileOut = open(f"{fileOutputPath}-fail.txt", "w")
  
  def __del__(self):
    if self._successFileOut is not None:
      self._successFileOut.close()

    if self._failFileOut is not None:
      self._failFileOut.close()
  
  def _successFile(self) -> TextIO:
    if self._successFileOut is None:
      return sys.stdout
    else:
      return self._successFileOut

  def _failFile(self) -> TextIO:
    if self._failFileOut is None:
      return sys.stderr
    else:
      return self._failFileOut
  
  def writeSuccess(self, string: str):
    print(string, file=self._successFile())

  def writeFail(self, string: str):
    print(string, file=self._failFile())