# Minecraft Addon URL Extractor

This script extracts URLs from a markdown file, then outputs a file download URLs for each [Modrinth](https://modrinth.com/) or [CurseForge](https://www.curseforge.com/minecraft) Minecraft project it encounters (if it can).  For now, project links are only pulled from Markdown files, but that can easily be expanded upon.

## Motivation

I made this project because I wanted to automate downloading Minecraft addons
*for a specific version of the game, in a platform-independent way, from multiple web sources.*
Both Modrinth and CurseForge have their own GUI clients, but I don't want to rely on those for
downloading and organizing Minecraft add-on content.

## Setup

This project requires a [Python](https://www.python.org/) interpreter to run.

1. Download dependencies: `pip install -r ./requirements.txt` or `pip install beautifulsoup4 playwright aiohttp[speedups]`
2. Run *main.py* with a Minecraft version argument and a markdown file path to pull URLs from. [See below for examples.](#running)

## Running

Output to files:

```sh
# Takes links from long-list.md and outputs successfully resolved download URLs
# to ./1.19.2-output-success.txt, and any failures or items which need manual
# download to ./1.19.2-output-fail.txt
python src/main.py '1.19.2' example-files/long-list.md -o ./1.19.2-output
```

Or output to *stdout* and *stderr*:

```sh
# Takes links from long-list.md and outputs successfully resolved download URLs
# to stdout, and any failures or items which need manual review to stderr.
python src/main.py '1.19.2' example-files/long-list.md
```
