import pandas as pd
import re
import json
import requests
from multiprocessing import Pool, Manager
import time
import os
import logging


class MangaListExtractor:
    def __init__(self, filename):
        """
        :param filename: Must pass a file. The two options are a .json or .msbf file.
        Functionality: If its a .msbf file it will read all the lines and store it as a list of lines. As for .json file
        it will read it as a list of dicts. This json file should be formatted with keys such as title, Kitsu ID, host,
        manga link, and ignore.
        """
        if filename.endswith(".msbf"):
            pd.set_option('display.max_rows', None)
            file = open(filename, "r", encoding="UTF-8")
            self.fileInfo = file.readlines()[1:]
            file.close()
            self.mangaList = []
        elif filename.endswith(".json"):
            self.mangaList = json.loads(filename)
            self.mangaDF = pd.DataFrame(self.mangaList)

    def get_manga_hosts(self):
        """
        Functionality: Will go through each line and parse for the host name while cutting it out and storing it into our dict list
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
        Functionality: Will go through each line and parse for the statuses of each of the manga while cutting it out
        and storing it into our list of dicts. This one is a bit different due to it using the REG of the status along
        with the weird numerical values found in those lines to better parse for them without taking part of the title.
        """
        mangaStatus = ["\tR\t[0-9]+.[0-9]+",
                       "\tY\t[0-9]+.[0-9]+",
                       "\tA\t[0-9]+.[0-9]+",
                       "\tN\t[0-9]+.[0-9]+"]
        for index, line in enumerate(self.fileInfo):
            for status in mangaStatus:
                r = re.search(status, line)
                if r is not None:
                    status_result = re.sub("[0-9]+\.[0-9]+", "", (re.sub("\t|\n", "", r[0])))
                    if status_result == "R":
                        self.mangaList[index]["Status"] = "current"
                    elif status_result == "Y":
                        self.mangaList[index]["Status"] = "completed"
                    elif status_result == "A":
                        self.mangaList[index]["Status"] = "on_hold"
                    elif status_result == "N":
                        self.mangaList[index]["Status"] = "dropped"
                    else:
                        self.mangaList[index]["Status"] = re.sub("[0-9]+\.[0-9]+", "",
                                                                 (re.sub("\t|\n", "", r[0])))
                    self.fileInfo[index] = re.sub(status, "", line)

    def get_manga_links(self):
        """
        Functionality: Will go through each line and parse for the links of each of the manga while cutting it out and
        storing it into our list of dicts.
        """
        linkregex = r'http(s)*://([A-Z]|[a-z]|[0-9]|\s|(\.)|/|-|_|\?|=|&)*'
        for index, line in enumerate(self.fileInfo):
            r = re.search(linkregex, line)
            if r is not None:
                self.mangaList[index]["Manga Link"] = re.sub("\t|\n", "", re.search(linkregex, line).group())
                self.fileInfo[index] = re.sub(linkregex, "", line)

    def get_manga_titles(self):
        """
        Functionality: As long as this function is excuted after all the above has then it will go through each line and
        just store the remaining string into our list of dicts.
        """
        for index, line in enumerate(self.fileInfo):
            self.mangaList[index]["Title"] = re.sub("\t|\n", "", line)

    def add_final_fields(self):
        """
        Functionality: This function is for adding the last fields that don't require any parsing of the original file
        contexts.
        """
        for manga in self.mangaList:
            manga["Kitsu ID"] = None
            manga["Ignore"] = False

    def get_manga_info(self):
        """
        Functionality: Simple function to excute all the required functions in the right order to get a complete list
        then put into a DataFrame.
        """
        self.get_manga_hosts()
        self.get_manga_statuses()
        self.get_manga_links()
        self.get_manga_titles()
        self.add_final_fields()
        self.mangaDF = pd.DataFrame(self.mangaList)

    def update_df(self):
        """
        Functionality: Simple function to call for updating the object's dataFrame whenever the user updates the
        mangaList.
        """
        self.mangaDF = pd.DataFrame(self.mangaList)

    def write_to_json(self, filename):
        """
        :param filename: This parameter requires the user to give a name for the file to be created/updated
        Functionality: This function is for writing a new json file with all the new opening filepath information as
        well as the old ones.
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
        """
        :param username: Username used for Kitsu to log in.
        :param password: Password used for Kitsu to log in.
        Funcationality: This will log in to the user's Kitsu account and grab all the necessary information to be used
        later on like the access token.
        """
        self.KitsuMangaList = []
        self.JSONMangaList = Manager().list()
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
        Functionality: Will get all the current manga the user has stored on their Kitsu Account.
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
        self.KitsuMangaList = self.KitsuMangaList + mangas["included"]
        print("Manga currently found from Kitsu: {}".format(len(self.KitsuMangaList)), end="\r")

        if "next" in mangas["links"]:
            while True:
                mangas = requests.get(mangas["links"]["next"]).json()
                if "next" in mangas["links"]:
                    self.KitsuMangaList = self.KitsuMangaList + mangas["included"]
                    print("Manga currently found from Kitsu: {}".format(len(self.KitsuMangaList)), end="\r")
                else:
                    self.KitsuMangaList = self.KitsuMangaList + mangas["included"]
                    print("Manga currently found from Kitsu: {}".format(len(self.KitsuMangaList)), end="\r")
                    break

    def manga_search(self, title):
        """
        :param title: The title of the manga series.
        :return: A list of dicts with a bunch of potential results matching that manga series.
        Functionality: Uses the manga title to retrieve information regarding that manga but this will result in a list
        of potential titles that match it.
        """
        result = requests.get("https://kitsu.io/api/edge/manga?filter[text]=" + title.replace(" ", "+")).json()
        return result

    def get_manga_id(self, index, manga):
        """
        :param index: Current index of manga within our list to keep track of the order of the manga within list to be
        used later.
        :param manga: This is a dict that contains information of our manga from the file it was retrieved from.
        Functionality: Goes through all the potential results the Kitsu website gives us after looking it up and doing
        its best to match it with the exact result.
        """
        if manga["Kitsu ID"] is None:
            result = self.manga_search(manga["Title"].replace("%", "%25"))
            logging.debug("Manga Currently being proceed: " + manga["Title"])

            try:
                if "data" in result and result["data"]:
                    titles = list(result["data"][0]["attributes"]["titles"].values())
                    matched = False
                    if titles:
                        for title in titles:
                            if title is not None:
                                if title.lower() == manga["Title"].lower():
                                    logging.debug("Index: " + str(index) + " " + manga["Title"] + " ID: " + result["data"][0]["id"])
                                    self.JSONMangaList.append({"Index": index, "Title": manga["Title"],
                                                               "Kitsu ID": result["data"][0]["id"]})
                                    matched = True
                                    break

                        if matched is False:
                            if result["data"][0]["attributes"]["abbreviatedTitles"]:
                                for AB_title in result["data"][0]["attributes"]["abbreviatedTitles"]:
                                    if AB_title is not None:
                                        if AB_title.lower() == manga["Title"].lower():
                                            logging.debug("Index: " + str(index) + " " + manga["Title"] + " ID: " + result["data"][0]["id"])
                                            self.JSONMangaList.append({"Index": index, "Title": manga["Title"],
                                                                       "Kitsu ID": result["data"][0]["id"]})
                                            matched = True

                            if matched is False:
                                logging.debug("Index: " + str(index) + " " + manga["Title"] + " ID: " + "N/A")
                                self.JSONMangaList.append({"Index": index, "Title": manga["Title"],
                                                           "Kitsu ID": None})
                else:
                    logging.debug("Index: " + str(index) + " " + manga["Title"] + " ID: " + "N/A")
                    self.JSONMangaList.append({"Index": index, "Title": manga["Title"],
                                               "Kitsu ID": None})

                logging.debug("Manga Finished being proceed: " + manga["Title"])

            except(KeyError, AttributeError, IndexError) as e:
                logging.debug("Manga Error: " + manga["Title"])
                logging.debug("Error type: " + e)
                logging.info("Error")
        else:
            logging.debug("Index: " + str(index) + " " + manga["Title"] + " ID: " + "N/A")
            self.JSONMangaList.append({"Index": index, "Title": manga["Title"],
                                       "Kitsu ID": manga["Kitsu ID"]})
        print("Manga's Finished Processing: {}".format(len(self.JSONMangaList)), end="\r")

    def get_manga_ids(self, mangaList):
        """
        :param mangaList: Takes a list of dicts of manga. This should typically be from the MangaExtractor.mangaList
        Functionality: This will use the multiprocessing based on however many cores the user has. It will take the
        mangaList is recieved and split it up among the processes and retrieve all the information it can get.
        """
        with Pool(os.cpu_count()) as p:
            p.starmap(self.get_manga_id, enumerate(mangaList))
        print("\n")

    def update_list(self, mangaList):
        """
        :param mangaList: Takes a list of dicts of manga. This should typically be from the MangaExtractor.mangaList
        :return: Returns that same list back for the user to manipulate later.
        Funcationality: Goes through the list of manga it recieved and updates it with the list of manga ids we got.
        """
        counter = 0
        for manga in self.JSONMangaList:
            if ((manga["Kitsu ID"] is not None) and (mangaList[manga["Index"]]["Title"] == manga["Title"]) and
               (mangaList[manga["Index"]]["Kitsu ID"] is None)):
                mangaList[manga["Index"]]["Kitsu ID"] = manga["Kitsu ID"]
                logging.debug("Updated {}, Index: {}".format(manga["Title"], manga["Index"]))
                counter = counter + 1
        print("Number of Manga IDs Updated: " + str(counter))

        return mangaList

    def drop_update(self):
        self.s = 1


    def request_test(self, something):
        self.test = requests.get(something).json()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    newList = MangaListExtractor("favorites.msbf")
    oldList = MangaListExtractor("favorites-old.msbf")
    newListKitsu = Kitsu("Kitsuneace", "Cookie100203")
    oldListKitsu = Kitsu("Kitsuneace", "Cookie100203")

    newList.get_manga_info()
    oldList.get_manga_info()

    newListKitsu.get_manga_ids(newList.mangaList)
    oldListKitsu.get_manga_ids(oldList.mangaList)

    newList.mangaList = newListKitsu.update_list(newList.mangaList)
    oldList.mangaList = oldListKitsu.update_list(oldList.mangaList)
    newList.update_df()
    oldList.update_df()

    comparer = MangaComparer(newList, oldList)
