import os
import re
import pandas as pd
from pandas import ExcelWriter
from difflib import SequenceMatcher
from tqdm import tqdm
from sys import platform
from multiprocessing import Pool, Manager, freeze_support

"""
Note: Currently works best on a Linux OS due to having multiprocessing capabilities. Windows is not able to do multiprocessing due to it
      not forking correctly (I think). In the meantime, use substitue script for Windows.
R - Reading
Y - Completed
A - Archived
N - Not Reading

------------------
TO DO
------------------
1. Get rid of JPN Title and change back ENG Title back to just Title. Don't think JPN Title will be necessary after some rethinking.
"""
newline_tabregex = r'\t|\n'
matchfilterregex = r'(\s|:|/|\?)*'
Linkregex = r'http(s)*://([A-Z]|[a-z]|[0-9]|\s|(\.)|/|-|_|\?|=|&)*'
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
resultchecker = 0
manager = Manager()
shared_list = manager.list()


# Function for clearing the screen
def clear_screen():
    if platform == "linux" or platform == "linux2" or platform == "darwin":
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

    print("Finding Manga Files")

    # Creating an empty list to use to iterate for multiprocessing and creating a pool of workers
    iteration = list(range(0, len(mangalist)))
    pool = Pool()
    for x in tqdm(pool.imap(get_outer, iteration), total=len(iteration)):
        pass
    pool.close()
    pool.join()

    # Multiprocessing does not share the global variables among the child processes so we store it in a shared variable and then put the new information
    # back to our mangalist.
    for x in range(len(shared_list)):
        mangalist[x] = shared_list[x]


# This is a basically the loop that would be found within a nested loop but was changed to multiprocessing could be implemented.
def get_outer(xy):
    # When using multiprocessing, the imap function passes a function and a list. This case xy is the list that we passed in to use as our iteration
    x = xy
    temp = mangalist[x]
    for y in range(len(mangafiles)):
        listname = re.sub(matchfilterregex, '', (mangalist[x]['Host'] + "_" + mangalist[x]['ENG Title'] + "_info.dat"))
        filename = re.sub(matchfilterregex, '', mangafiles[y])
        matcher = SequenceMatcher(None, listname, filename)
        if matcher.ratio() == 1:
            temp['File'] = mangafiles[y]
            shared_list.append(temp)
            resultchecker = 0
            break
        else:
            resultchecker = 1
            continue
    if resultchecker == 1:
        temp['File'] = "No File Found"
        shared_list.append(temp)


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
            file = open(mangalist[x]['Host'] + "/" + mangalist[x]['File'], encoding="UTF-8")
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
                tempchap = re.sub(r'_', '0', tempchap)
                tempchap = tempchap.replace(' ', '')

                if curchapter < float(re.search(r'(([0-9]+|\.)*)', tempchap).group(1)):
                    curchapter = float(re.search(r'(([0-9]+|\.)*)', tempchap).group(1))

                else:
                    continue
            temp['Current Chapter'] = curchapter
            mangalist[x] = temp


# Writing the dataframe to .xlsx file
def save_excel(dataframe, excelName):
    # Check if our mangalist already exists
    # If it does exist we will extract some information from it and merging it with out new MangaList
    if os.path.exists(excelName.replace(" ", "") + ".xlsx") is True:
        # Reading preexisting MangaList file and extracting specific information from it
        df_temp = pd.read_excel(excelName.replace(" ", "") + ".xlsx", sheet_name=excelName)
        df_extract = df_temp[['ENG Title', 'JPN Title', 'Kitsu Link']].copy()

        # Updating our dataframe with our existing shell file
        dataframe = pd.merge(dataframe, df_extract, how='outer', on=['ENG Title']).drop(['JPN Title_x', 'Kitsu Link_x'], axis=1)
        dataframe = dataframe[['ENG Title', 'JPN Title_y', 'Status', 'Current Chapter', 'Host', 'Manga Link', 'Kitsu Link_y', 'File']]
        dataframe = dataframe.rename(index=str, columns={"JPN Title_y": "JPN Title", "Kitsu Link_y": "Kitsu Link"})
        dataframe = dataframe.drop_duplicates(subset=['ENG Title', 'JPN Title', 'Status', 'Current Chapter', 'Host', 'Manga Link', 'Kitsu Link', 'File'], keep='first')
        dataframe['Status'] = pd.Categorical(dataframe['Status'], ["R", "Y", "A"])
        dataframe['Test'] = dataframe['ENG Title'].str.lower()
        dataframe = dataframe.sort_values(['Status', 'Test'])
        dataframe.drop('Test', axis=1, inplace=True)
        dataframe.reset_index(drop=True, inplace=True)

        # Now writing to our dataframe to .xlsx file after updating it with the shell file
        writer = ExcelWriter(excelName.replace(" ", "") + ".xlsx", encoding="UTF-8")
        dataframe.to_excel(writer, excelName, encoding="UTF-8")
        writer.save()

    else:
        # Now writing to our dataframe to .xlsx file
        writer = ExcelWriter(excelName.replace(" ", "") + ".xlsx", encoding="UTF-8")
        dataframe.to_excel(writer, excelName, encoding="UTF-8")
        writer.save()

    return dataframe


if __name__ == '__main__':
    freeze_support()
    os.chdir('..')
    os.chdir("Manga Storm/Container/Documents/UserData/")
    top = os.getcwd()

    file = open("favorites.dat", "r", encoding="UTF-8")
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
    df = save_excel(df, "Manga List")

    print(df)
