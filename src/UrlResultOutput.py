# from io import TextIOWrapper, TextIOBase
from typing import TextIO
import sys
from Helpers import printStderr

class UrlResultOutput:
  successFileOut: TextIO | None = None
  failFileOut: TextIO | None = None

  def __init__(self, fileOutputPath: str | None = None):
    if fileOutputPath is not None:
      self.successFileOut = open(f"{fileOutputPath}-success.txt", "w")
      self.failFileOut = open(f"{fileOutputPath}-fail.txt", "w")
  
  def __del__(self):
    if self.successFileOut is not None:
      self.successFileOut.close()

    if self.failFileOut is not None:
      self.failFileOut.close()
  
  def _successFile(self) -> TextIO:
    if self.successFileOut is None:
      return sys.stdout
    else:
      return self.successFileOut

  def _failFile(self) -> TextIO:
    if self.failFileOut is None:
      return sys.stderr
    else:
      return self.failFileOut
  
  def outputSuccess(self, string: str):
    print(string, file=self._successFile())

  def outputFail(self, string: str):
    print(string, file=self._failFile())