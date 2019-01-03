import os
import re
from pprint import pprint
import pandas as pd

"""
R - Reading
Y - Completed
A - Archived
N - Not Reading
"""
newline_tabregex = r'\t|\n'
Linkregex = r'http(s)*://([A-Z]|[a-z]|[0-9]|\s|(\.)|/|-|_)*'
Rstatusregex = r'\tR\t[0-9]+.[0-9]+'
Ystatusregex = r'\tY\t[0-9]+.[0-9]+'
Astatusregex = r'\tA\t[0-9]+.[0-9]+'
Nstatusregex = r'\tN\t[0-9]+.[0-9]+'
mangadexregex = r'z13mangadex'
mangahereregex = r'z03mangahere'
mangatownregex = r'z09mangatown'
mangafoxregex = r'mangafox'
mangareaderregex = r'mangareader'
mangahomeregex = r'mangahome'
mangapandaregex = r'z05mangapanda'
kissmangaregex = r'z06kissmanga'
readmangatodayregex = r'z10readmangatoday'
mangakoiregex = r'z12mangakoi'
mangaedenregex = r'z01mangaeden'
mangafoxmbregex = r'mangafoxmb'
mangainfo = {'Title': "", 'Current Chapter': "", 'Status': "", 'Host': "", 'Link': ""}
mangalist = []
lines2 = []

os.chdir('..')
os.chdir("Manga Storm/Container/Documents/UserData/")

file = open("favorites2.dat", "r")
lines = file.readlines()

# Reading through each line and parsing each line for mangatype and cutting it out and storing it
for x in range(len(lines)):
    r = re.search(mangadexregex, lines[x])
    if r is not None:
        mangainfo['Host'] = "mangadex"
        mangalist.append(mangainfo.copy())
        lines2.append(re.sub(mangadexregex, '', lines[x]))

    r = re.search(mangahereregex, lines[x])
    if r is not None:
        mangainfo['Host'] = "mangahere"
        mangalist.append(mangainfo.copy())
        lines2.append(re.sub(mangahereregex, '', lines[x]))

    r = re.search(mangatownregex, lines[x])
    if r is not None:
        mangainfo['Host'] = "mangatown"
        mangalist.append(mangainfo.copy())
        lines2.append(re.sub(mangatownregex, '', lines[x]))

    r = re.search(mangafoxregex, lines[x])
    if r is not None:
        mangainfo['Host'] = "mangafox"
        mangalist.append(mangainfo.copy())
        lines2.append(re.sub(mangafoxregex, '', lines[x]))

    r = re.search(mangareaderregex, lines[x])
    if r is not None:
        mangainfo['Host'] = "mangareader"
        mangalist.append(mangainfo.copy())
        lines2.append(re.sub(mangareaderregex, '', lines[x]))

    r = re.search(mangahomeregex, lines[x])
    if r is not None:
        mangainfo['Host'] = "mangahome"
        mangalist.append(mangainfo.copy())
        lines2.append(re.sub(mangahomeregex, '', lines[x]))

    r = re.search(mangapandaregex, lines[x])
    if r is not None:
        mangainfo['Host'] = "mangapanda"
        mangalist.append(mangainfo.copy())
        lines2.append(re.sub(mangapandaregex, '', lines[x]))

    r = re.search(kissmangaregex, lines[x])
    if r is not None:
        mangainfo['Host'] = "kissmanga"
        mangalist.append(mangainfo.copy())
        lines2.append(re.sub(kissmangaregex, '', lines[x]))

    r = re.search(readmangatodayregex, lines[x])
    if r is not None:
        mangainfo['Host'] = "readmangatoday"
        mangalist.append(mangainfo.copy())
        lines2.append(re.sub(readmangatodayregex, '', lines[x]))

    r = re.search(mangakoiregex, lines[x])
    if r is not None:
        mangainfo['Host'] = "mangakoi"
        mangalist.append(mangainfo.copy())
        lines2.append(re.sub(mangakoiregex, '', lines[x]))

    r = re.search(mangaedenregex, lines[x])
    if r is not None:
        mangainfo['Host'] = "mangaeden"
        mangalist.append(mangainfo.copy())
        lines2.append(re.sub(mangaedenregex, '', lines[x]))

    r = re.search(mangafoxmbregex, lines[x])
    if r is not None:
        mangainfo['Host'] = "mangafoxmb"
        mangalist.append(mangainfo.copy())
        lines2.append(re.sub(mangafoxmbregex, '', lines[x]))

# Reading through each line and parsing each line for manga status and cutting it out and storing it
del lines[:]
for x in range(len(lines2)):
    r = re.search(Rstatusregex, lines2[x])
    if r is not None:
        temp = mangalist[x]
        temp['Status'] = "R"
        mangalist[x] = temp
        lines.append(re.sub(Rstatusregex, '', lines2[x]))

    r = re.search(Ystatusregex, lines2[x])
    if r is not None:
        temp = mangalist[x]
        temp['Status'] = "Y"
        mangalist[x] = temp
        lines.append(re.sub(Ystatusregex, '', lines2[x]))

    r = re.search(Astatusregex, lines2[x])
    if r is not None:
        temp = mangalist[x]
        temp['Status'] = "A"
        mangalist[x] = temp
        lines.append(re.sub(Astatusregex, '', lines2[x]))

    r = re.search(Nstatusregex, lines2[x])
    if r is not None:
        temp = mangalist[x]
        temp['Status'] = "N"
        mangalist[x] = temp
        lines.append(re.sub(Nstatusregex, '', lines2[x]))

# Reading through each line and parsing each line for website link and cutting it out and storing it
del lines2[:]
for x in range(len(lines)):
    r = re.search(Linkregex, lines[x])
    if r is not None:
        temp = mangalist[x]
        temp['Link'] = re.search(Linkregex, lines[x]).group()
        mangalist[x] = temp
        lines2.append(re.sub(Linkregex, '', lines[x]))

# Reading through each line while removing newlines and tabs
del lines[:]
for x in range(len(lines2)):
    temp = mangalist[x]
    temp['Title'] = re.sub(newline_tabregex, '', lines2[x])
    mangalist[x] = temp

print(os.getcwd())
print(pd.DataFrame(mangalist, columns=['Title', 'Status', 'Current Chapter', 'Host', 'Link']).to_string())
