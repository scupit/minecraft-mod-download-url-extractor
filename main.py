import sys

if len(sys.argv) > 1:
  print("Additional arguments: ")
  for x in range(1, len(sys.argv)):
    print("\t", sys.argv[x])
else:
  print("No additional arguments passed to python script...")
