import os
import re
import pandas as pd
import numpy as np
from pandas import ExcelWriter
from difflib import SequenceMatcher
from tqdm import tqdm
from sys import platform

"""
Note: Currently works best on a Linux OS than Windows OS because on Windows it cannot read unicode characters well which results in the .dat file not
      being found.
R - Reading
Y - Completed
A - Archived
N - Not Reading
"""
newline_tabregex = r'\t|\n'
matchfilterregex = r'(\s|:|/|\?)*'
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
mangainfo = {'ENG Title': "", 'JPN Title:': "", 'Current Chapter': "", 'Status': "", 'Host': "", 'Manga Link': "", 'Kitsu Link': "", 'File': ""}
mangalist = []
mangafiles = []
lines2 = []


# Function for clearing the screen
def clear_screen():
    if platform == "linux" or platform == "linux2":
        OScommand = 'clear'

    elif platform == "win32" or platform == "win64":
        OScommand = 'cls'

    else:
        print("Could Not Detect Operating System")
    os.system(OScommand)


# Reading through each line and parsing each line for mangatype and cutting it out and storing it
def get_hosts():
    for x in range(len(lines)):
        r = re.search(mangadexregex, lines[x])
        if r is not None:
            mangainfo['Host'] = mangadexregex
            mangalist.append(mangainfo.copy())
            lines2.append(re.sub(mangadexregex, '', lines[x]))

        r = re.search(mangahereregex, lines[x])
        if r is not None:
            mangainfo['Host'] = mangahereregex
            mangalist.append(mangainfo.copy())
            lines2.append(re.sub(mangahereregex, '', lines[x]))

        r = re.search(mangatownregex, lines[x])
        if r is not None:
            mangainfo['Host'] = mangatownregex
            mangalist.append(mangainfo.copy())
            lines2.append(re.sub(mangatownregex, '', lines[x]))

        r = re.search(mangafoxregex, lines[x])
        if r is not None:
            mangainfo['Host'] = mangafoxregex
            mangalist.append(mangainfo.copy())
            lines2.append(re.sub(mangafoxregex, '', lines[x]))

        r = re.search(mangareaderregex, lines[x])
        if r is not None:
            mangainfo['Host'] = mangareaderregex
            mangalist.append(mangainfo.copy())
            lines2.append(re.sub(mangareaderregex, '', lines[x]))

        r = re.search(mangahomeregex, lines[x])
        if r is not None:
            mangainfo['Host'] = mangahomeregex
            mangalist.append(mangainfo.copy())
            lines2.append(re.sub(mangahomeregex, '', lines[x]))

        r = re.search(mangapandaregex, lines[x])
        if r is not None:
            mangainfo['Host'] = mangapandaregex
            mangalist.append(mangainfo.copy())
            lines2.append(re.sub(mangapandaregex, '', lines[x]))

        r = re.search(kissmangaregex, lines[x])
        if r is not None:
            mangainfo['Host'] = kissmangaregex
            mangalist.append(mangainfo.copy())
            lines2.append(re.sub(kissmangaregex, '', lines[x]))

        r = re.search(readmangatodayregex, lines[x])
        if r is not None:
            mangainfo['Host'] = readmangatodayregex
            mangalist.append(mangainfo.copy())
            lines2.append(re.sub(readmangatodayregex, '', lines[x]))

        r = re.search(mangakoiregex, lines[x])
        if r is not None:
            mangainfo['Host'] = mangakoiregex
            mangalist.append(mangainfo.copy())
            lines2.append(re.sub(mangakoiregex, '', lines[x]))

        r = re.search(mangaedenregex, lines[x])
        if r is not None:
            mangainfo['Host'] = mangaedenregex
            mangalist.append(mangainfo.copy())
            lines2.append(re.sub(mangaedenregex, '', lines[x]))

        r = re.search(mangafoxmbregex, lines[x])
        if r is not None:
            mangainfo['Host'] = mangafoxmbregex
            mangalist.append(mangainfo.copy())
            lines2.append(re.sub(mangafoxmbregex, '', lines[x]))


# Reading through each line and parsing each line for manga status and cutting it out and storing it
def get_status():
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
def get_mangalink():
    del lines2[:]
    for x in range(len(lines)):
        r = re.search(Linkregex, lines[x])
        if r is not None:
            temp = mangalist[x]
            temp['Manga Link'] = re.sub(newline_tabregex, '', re.search(Linkregex, lines[x]).group())
            mangalist[x] = temp
            lines2.append(re.sub(Linkregex, '', lines[x]))


# Reading through each line while removing newlines and tabs
def get_engtitle():
    del lines[:]
    for x in range(len(lines2)):
        temp = mangalist[x]
        temp['ENG Title'] = re.sub(newline_tabregex, '', lines2[x])
        mangalist[x] = temp


# Finding all .dat files for manga information and storing the file name
def get_mangafiles():
    # Grabbing all .dat files in directory and subdirectory
    for root, dirs, files in os.walk(top):
        for file in files:
            if file.endswith(".dat"):
                mangafiles.append(file)

    del lines[:]
    del lines2[:]
    resultchecker = 0
    print("Finding Manga Files")
    for x in tqdm(range(len(mangalist))):
        temp = mangalist[x]
        for y in range(len(mangafiles)):
            listname = re.sub(matchfilterregex, '', (mangalist[x]['Host'] + "_" + mangalist[x]['ENG Title'] + "_info.dat"))
            filename = re.sub(matchfilterregex, '', mangafiles[y])
            matcher = SequenceMatcher(None, listname, filename)
            if matcher.ratio() == 1:
                temp['File'] = mangafiles[y]
                mangalist[x] = temp
                resultchecker = 0
                break
            else:
                resultchecker = 1
                continue
        if resultchecker == 1:
            temp['File'] = "No File Found"
            mangalist[x] = temp


# Goes through each manga .dat file that was found and runs multiple regexes to find the highest finished chapter
def get_mangachapters():
    print("Finding Manga Chapters")
    clear_screen()
    for x in tqdm(range(len(mangalist))):
        if mangalist[x]['File'] == "No File Found":
            temp = mangalist[x]
            temp['Current Chapter'] = "N/A"
            mangalist[x] = temp

        if mangalist[x]['File'] != "No File Found":
            temp = mangalist[x]
            file = open(mangalist[x]['Host'] + "/" + mangalist[x]['File'])
            lines = file.readlines()
            file.close()

            """
            These regular expressions are for filtering the different types of formats for different manga series
            1. Is for filtering out the ID found in each file
            2. Is for filtering series that has chapters labeled with VOL number. Example: VOL5 34
            3. Is for filtering series where there are duplicate chapters which uses a -2 in the chapter name. Example: 44-2
            4. Is for filtering series where there are duplicate chapters which uses the title in the chapter name with the chapter number. Example: Ao-12
            5. Is for filtering series where there are duplicate chapters which uses the title in the chapter name but for the first chapter doesn't
                use the chapter number. Which is replaced with a value of 0. Example: Ao
            6. Is for filtering series where after running the other regexes can result in a string of 0.0.- which is replaced by a zero value.
            7. Is for filtering series where after running the other regexes can result in a string of 0.0. which is replaced by a zero value.
            """
            tempchap = re.sub(r'[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]\.[0-9][0-9][0-9][0-9][0-9][0-9]', '', lines[2])
            tempchap = re.sub(r'(([A-Z]|[a-z])+[0-9]+)\s', '', tempchap)
            tempchap = re.sub(r'[0-9]+-[0-9]+', '0', tempchap)
            tempchap = re.sub(r'([A-Z]|[a-z])+-', '', tempchap)
            tempchap = re.sub(r'([A-Z]|[a-z])+', '0', tempchap)
            tempchap = re.sub(r'0\.0\.-', '0', tempchap)
            tempchap = re.sub(r'0\.0\.', '0', tempchap)
            tempchap = tempchap.replace(' ', '')

            curchapter = float(re.search(r'(([0-9]+|\.)*)', tempchap).group(1))

            # We start at index 3 so we can skip the first 3 lines in the .dat file which only gives information about the manga and not the chapters we need.
            for y in range(3, len(lines)):
                tempchap = re.sub(r'[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]\.[0-9][0-9][0-9][0-9][0-9][0-9]', '', lines[y])
                tempchap = re.sub(r'(([A-Z]|[a-z])+[0-9]+)\s', '', tempchap)
                tempchap = re.sub(r'[0-9]+-[0-9]+', '0', tempchap)
                tempchap = re.sub(r'([A-Z]|[a-z])+-', '', tempchap)
                tempchap = re.sub(r'([A-Z]|[a-z])+', '0', tempchap)
                tempchap = re.sub(r'0\.0\.-', '0', tempchap)
                tempchap = re.sub(r'0\.0\.', '0', tempchap)
                tempchap = tempchap.replace(' ', '')

                if curchapter < float(re.search(r'(([0-9]+|\.)*)', tempchap).group(1)):
                    curchapter = float(re.search(r'(([0-9]+|\.)*)', tempchap).group(1))

                else:
                    continue
            temp['Current Chapter'] = curchapter
            mangalist[x] = temp


# Writing the dataframe to .xlsx file
def save_excel(dataframe, excelName):
    # Check if our mangalist shell exists
    if os.path.exists(excelName.replace(" ", "") + "_Shell" + ".xlsx") is True:
        df_shell = pd.read_excel(excelName.replace(" ", "") + "_Shell" + ".xlsx", sheet_name='Shell')

        # Updating our dataframe with our existing shell file
        dataframe.update(df_shell)
        dataframe['Status'] = pd.Categorical(dataframe['Status'], ["R", "Y", "A"])
        dataframe = dataframe.sort_values(['Status', 'ENG Title'])
        dataframe = dataframe.reset_index(drop=True)

        # Now writing to our dataframe to .xlsx file after updating it with the shell file
        writer = ExcelWriter(excelName.replace(" ", "") + ".xlsx")
        dataframe.to_excel(writer, excelName)
        writer.save()

        # Now rewriting to our shell file by extracting those columns again but we do this in case of new manga has been added so we
        # can have that in our shell
        df_shell = dataframe[['ENG Title', 'JPN Title', 'Kitsu Link']].copy()
        writer = ExcelWriter(excelName.replace(" ", "") + "_Shell" + ".xlsx")
        df_shell.to_excel(writer, excelName)
        writer.save()

    else:
        # Since it did not exist we will create one
        df_shell = dataframe[['ENG Title', 'JPN Title', 'Kitsu Link']].copy()
        writer = ExcelWriter(excelName.replace(" ", "") + "_Shell" + ".xlsx")
        df_shell.to_excel(writer, excelName)
        writer.save()

        # Now writing to our dataframe to .xlsx file
        writer = ExcelWriter(excelName.replace(" ", "") + ".xlsx")
        dataframe.to_excel(writer, excelName)
        writer.save()

    return dataframe


if __name__ == "__main__":
    os.chdir('..')
    os.chdir("Manga Storm/Container/Documents/UserData/")
    top = os.getcwd()

    file = open("favorites2.dat", "r")
    lines = file.readlines()
    file.close()

    get_hosts()
    get_status()
    get_mangalink()
    get_engtitle()
    get_mangafiles()
    get_mangachapters()

    clear_screen()

    df = pd.DataFrame(mangalist, columns=['ENG Title', 'JPN Title', 'Status', 'Current Chapter', 'Host', 'Manga Link', 'Kitsu Link', 'File'])

    print(save_excel(df, "Manga List"))
