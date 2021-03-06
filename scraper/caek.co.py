# Scraper for "caek.co"

import re
import requests
import json
import datetime


from lxml import html


BASE_URL = "https://caek.co/"
CHAPTER_REGEX = re.compile(r"^ch(\d*)(.*)")


class Manga:
    __slots__ = ("name", "weblink", "chapters")
    def __init__(self, data):
        self.name = data.xpath("./text()")[0]
        self.weblink = BASE_URL + data.xpath("./@href")[0]
        self.chapters = []

    def __str__(self):
        return self.name

    def setChapters(self, chapters: list):
        self.chapters = chapters


class Chapter:
    __slots__ = ("index", "name", "volume", "weblink", "pages")
    def __init__(self, index, weblink, name = None, volume = 0, pages = []):
        self.index = index
        self.name = name
        self.volume = volume
        self.weblink = BASE_URL + weblink
        self.pages = [self.weblink + "/" + p for p in pages if str(p).endswith("g")]

    def __str__(self):
        return self.name


def getMangaList():
    init = requests.get(BASE_URL)
    tree = html.fromstring(init.text)
    mangas = tree.xpath("//li/a")
    mangaList = []
    for i in mangas:
        manga = Manga(i)
        if str(manga).startswith("_"):
            continue
        mangaList.append(manga) 
    return mangaList


def getMangaChapters(number: int=None):
    mangaList = getMangaList()
    if number is None:
        # Manually select manga if number not specified
        for index, manga in enumerate(mangaList):
            print(str(index) + ":", manga.name)
        number = int(input("Select manga you want to scrape: "))
    chosen = mangaList[number]

    # Get all chapters
    # TODO: Cache/Log already processed chapter, to reduce requests
    init = requests.get(chosen.weblink)
    tree = html.fromstring(init.text)
    tempChapters = [c for c in tree.xpath("//li/a") if str(c.xpath("./text()")[0]).startswith("ch")]
    chapters = []
    for i, c in enumerate(tempChapters):
        chapter = c.xpath("./text()")[0]
        regex = CHAPTER_REGEX.search(chapter)
        name = regex[2]
        if name.startswith(" "):
            name = name[1:]
        index = regex[1]
        print("Getting chapter [{}/{}]".format(i+1, len(tempChapters)), end="\r")
        weblink = c.xpath("./@href")[0]

        # Get all pages
        init = requests.get(BASE_URL + weblink)
        tree = html.fromstring(init.text)
        pages = tree.xpath("//a/img/@src")

        chapter = Chapter(index, weblink, name, 0, pages)

        chapters.append(chapter)

    chosen.setChapters(chapters)
    return chosen


def cubarify(manga: Manga, _print: bool=False):
    # Template for cubari json file
    # TODO: Cache/Log already processed manga, so only chapters will be printed/returned
    result = {
        "chapters": {},
        "title": manga.name,
        "description": "",
        "artist": "",
        "author": "",
        "cover": ""
    }

    for chapter in reversed(manga.chapters):
        chapterDict = {
            "title": chapter.name,
            "volume": str(chapter.volume),
            "groups": {
                "Waterflame Scans": [page for page in chapter.pages]
            },
            "last_updated": datetime.datetime.now().timestamp()
        }
        result["chapters"][chapter.index] = chapterDict

    if _print:
        print(json.dumps(result, indent=4))
    return result


if __name__ == "__main__":
    manga = getMangaChapters()
    cubarify(manga, True)
