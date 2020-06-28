import pandas as pd
import re
import json
import requests
import threading

class MangaListExtractor:
    def __init__(self, filename):
        pd.set_option('display.max_rows', None)
        file = open(filename, "r", encoding="UTF-8")
        self.fileInfo = file.readlines()[1:]
        file.close()
        self.mangaList = []

    def get_manga_hosts(self):
        """
        Will go through each line and parse for the host name while cutting it out and storing it into our dict list
        """
        mangaHost = ["z13mangadex",
                     "z03mangahere",
                     "z09mangatown",
                     "mangafoxmb",
                     "mangareader",
                     "z12mangakoi",
                     "mangahome",
                     "z05mangapanda",
                     "z06kissmanga",
                     "z10readmangatoday",
                     "z01mangaeden",
                     "mangafox"]

        for index, line in enumerate(self.fileInfo):
            for host in mangaHost:
                r = re.search(host, line)
                if r is not None:
                    self.mangaList.append({"Host": host})
                    self.fileInfo[index] = re.sub(host, '', line)
                    break

    def get_manga_statuses(self):
        """
        Will go through each line and parse for the statuses of each of the manga while cutting it out and storing it into
        our list of dicts. This one is a bit different due to it using the REG of the status along with the weird numerical
        values found in those lines to better parse for them without taking part of the title.
        """
        mangaStatus = ["\tR\t[0-9]+.[0-9]+",
                       "\tY\t[0-9]+.[0-9]+",
                       "\tA\t[0-9]+.[0-9]+",
                       "\tN\t[0-9]+.[0-9]+"]
        for index, line in enumerate(self.fileInfo):
            for status in mangaStatus:
                r = re.search(status, line)
                if r is not None:
                    self.mangaList[index]["Status"] = re.sub("[0-9]+\.[0-9]+", "",
                                                             (re.sub("\t|\n", "", r[0])))
                    self.fileInfo[index] = re.sub(status, "", line)

    def get_manga_links(self):
        """
        Will go through each line and parse for the links of each of the manga while cutting it out and storing it into
        our list of dicts.
        """
        linkregex = r'http(s)*://([A-Z]|[a-z]|[0-9]|\s|(\.)|/|-|_|\?|=|&)*'
        for index, line in enumerate(self.fileInfo):
            r = re.search(linkregex, line)
            if r is not None:
                self.mangaList[index]["Manga Link"] = re.sub("\t|\n", "", re.search(linkregex, line).group())
                self.fileInfo[index] = re.sub(linkregex, "", line)

    def get_manga_titles(self):
        """
        As long as this function is excuted after all the above has then it will go through each line and just store the
        remaining string into our list of dicts.
        """
        for index, line in enumerate(self.fileInfo):
            self.mangaList[index]["Title"] = re.sub("\t|\n", "", line)
            self.mangaList[index]["Alternative Titles"] = []

    def add_final_fields(self):
        """
        This function is for adding the last fields that don't require any parsing of the original file contexts.
        """
        for manga in self.mangaList:
            manga["Kitsu ID"] = None
            manga["Ignore"] = False


    def get_manga_info(self):
        """
        Simple function to excute all the required functions in the right order to get a complete list then put into a
        DataFrame.
        """
        self.get_manga_hosts()
        self.get_manga_statuses()
        self.get_manga_links()
        self.get_manga_titles()
        self.add_final_fields()
        self.mangaDF = pd.DataFrame(self.mangaList)

    def get_manga_from_json(self):
        """
        Will read from a json file that is formatted like our json file when writing our list to one. This is read old
        lists and compare/merge later.
        """
        self.s = 1

    def write_to_json(self, filename):
        """
        filename: This parameter requires the user to give a name for the file to be created/updated
        This function is for writing a new json file with all the new opening filepath information as well as the old ones.
        """
        with open(filename, "w") as jsonFile:
            jsonFile.seek(0)
            json.dump(self.mangaList, jsonFile, indent=4, ensure_ascii=False)
            jsonFile.truncate()
            print(filename + " has been updated/created.")


class MangaComparer:
    def __init__(self, newMangaList, oldMangaList):
        self.newList = newMangaList.mangaDF
        self.oldList = oldMangaList.mangaDF

    def find_differences(self):
        """
        This function will find the titles that were not found in the old list from the new list.
        """
        rows_to_be_dropped = []
        for newList_index, newList_row in self.newList.iterrows():
            similarities = self.oldList.loc[(self.oldList["Title"] == newList_row["Title"]) &
                                            (self.oldList["Host"] == newList_row["Host"])]
            if not similarities.empty:
                rows_to_be_dropped.append(newList_index)
        differences = self.newList.drop(index=rows_to_be_dropped)


class Kitsu:
    def __init__(self, username, password):
        self.mangaList = []
        self.url = "https://kitsu.io/api"
        getTokenurl = "/oauth/token?grant_type=password&username=<username>&password=<password>"
        getTokenurl = getTokenurl.replace("<username>", username)
        getTokenurl = getTokenurl.replace("<password>", password)
        jsonInfo = requests.post(self.url + getTokenurl).json()
        self.access_token = jsonInfo["access_token"]
        self.token_type = jsonInfo["token_type"]
        self.header = {"Authorization": self.token_type + ' ' + self.access_token}
        self.user_id = requests.get(self.url + "/edge/users?filter[self]=true",
                                    headers=self.header).json()["data"][0]["id"]

    def get_current_library_entries(self):
        """
        Will get all the current manga the user has stored on their Kitsu Account.
        1. filter[kind]=manga - This specify what library we want to look at it be anime or manga.
        2. filter[user_id]= user_id - This is whoses library to look at.
        3. fields[libraryEntries]=id - When doing this GET requests it includes a bunch of garbage we don't need that
           has a lot of fields. So this is to make it more bearable by limiting it to display only the id field.
        4. include=manga - This is to actually get the manga information for all of them.
        5. fields[manga]=titles,status - This is to limit the fields from our mangas we get to just the titles and
           statuses.
        6.  page[limit]=500 - By default it will only show 10 mangas per page so changing it to 500 to get the max
            amount per page to speed up the time we're navigating through pages collecting all the manga infomation.
        """
        mangas = requests.get(self.url + "/edge/library-entries?filter[kind]=manga&filter[user_id]="
                              + self.user_id + "&fields[libraryEntries]=id" + "&include=manga"
                              + "&fields[manga]=titles,status" + "&page[limit]=500", headers=self.header).json()
        self.mangaList = self.mangaList + mangas["included"]
        print("Manga currently found from Kitsu: {}".format(len(self.mangaList)), end="\r")

        if "next" in mangas["links"]:
            while True:
                mangas = requests.get(mangas["links"]["next"]).json()
                if "next" in mangas["links"]:
                    self.mangaList = self.mangaList + mangas["included"]
                    print("Manga currently found from Kitsu: {}".format(len(self.mangaList)), end="\r")
                else:
                    self.mangaList = self.mangaList + mangas["included"]
                    print("Manga currently found from Kitsu: {}".format(len(self.mangaList)), end="\r")
                    break

    def manga_search(self, title):
        self.result = requests.get("https://kitsu.io/api/edge/manga?filter[text]=" + title.replace(" ", "+")).json()

    def request_test(self, something):
        self.test = requests.get(something).json()


if __name__ == '__main__':
    newList = MangaListExtractor("favorites.msbf")
    oldList = MangaListExtractor("favorites-old.msbf")
    newList.get_manga_info()
    oldList.get_manga_info()
    comparer = MangaComparer(newList, oldList)
    kitsuUpdate = Kitsu("Kitsuneace", "Cookie100203")
