import os
import re

"""
"""
mangadexregex = re.compile('z13mangadex', re.IGNORECASE)
mangahereregex = re.compile('z03mangahere', re.IGNORECASE)
mangatownregex = re.compile('z09mangatown', re.IGNORECASE)
mangafoxregex = re.compile('mangafox', re.IGNORECASE)
mangareaderregex = re.compile('mangareader', re.IGNORECASE)
mangahomeregex = re.compile('mangahome', re.IGNORECASE)
mangapandaregex = re.compile('z05mangapanda', re.IGNORECASE)
kissmangaregex = re.compile('z06kissmanga', re.IGNORECASE)
readmangatodayregex = re.compile('z10readmangatoday', re.IGNORECASE)
mangakoiregex = re.compile('z12mangakoi', re.IGNORECASE)
mangaedenregex = re.compile('z01mangaeden', re.IGNORECASE)
mangafoxmbregex = re.compile('mangafoxmb', re.IGNORECASE)
mangatype = []

os.chdir('..')
os.chdir("Manga Storm/Container/Documents/UserData/")

file = open("favorite.dat", "r")
lines = file.readlines()

for x in range(len(lines)):
    r = re.search(mangadexregex, lines[x])
    if r is not None:
        mangatype.append("mangadex")

    r = re.search(mangahereregex, lines[x])
    if r is not None:
        mangatype.append("mangahere")

    r = re.search(mangatownregex, lines[x])
    if r is not None:
        mangatype.append("mangatown")

    r = re.search(mangafoxregex, lines[x])
    if r is not None:
        mangatype.append("mangafox")

    r = re.search(mangareaderregex, lines[x])
    if r is not None:
        mangatype.append("mangareader")

    r = re.search(mangahomeregex, lines[x])
    if r is not None:
        mangatype.append("mangahome")

    r = re.search(mangapandaregex, lines[x])
    if r is not None:
        mangatype.append("mangapanda")

    r = re.search(kissmangaregex, lines[x])
    if r is not None:
        mangatype.append("kissmanga")

    r = re.search(readmangatodayregex, lines[x])
    if r is not None:
        mangatype.append("readmangatoday")

    r = re.search(mangakoiregex, lines[x])
    if r is not None:
        mangatype.append("mangakoi")

    r = re.search(mangaedenregex, lines[x])
    if r is not None:
        mangatype.append("mangaeden")

    r = re.search(mangafoxmbregex, lines[x])
    if r is not None:
        mangatype.append("mangafoxmb")

print(os.getcwd())
print(lines[2])
print(len(lines))
print(len(mangatype))
