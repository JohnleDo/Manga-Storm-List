# TODO: Fix some print statements to be neater throughout the program
# TODO: Fix lines where it exceeds the character limit
# TODO: Have better naming scheme
# TODO: Use list comphrension for for loops
# TODO: Add error checking
import pandas as pd
import re
import json
import requests
from multiprocessing import Pool, Manager
import datetime
import os
import logging
import getpass


class MangaListExtractor:
    def __init__(self, filename):
        """
        Functionality: If its a .msbf file it will read all the lines and store it as a list of lines. As for .json file
        it will read it as a list of dicts. This json file should be formatted with keys such as title, Kitsu ID, host,
        manga link, and ignore.
        :param filename: Must pass a file. The two options are a .json or .msbf file.
        :return: None
        """
        if filename.endswith(".msbf"):
            pd.set_option('display.max_rows', None)
            file = open(filename, "r", encoding="UTF-8")
            self.fileInfo = file.readlines()[1:]
            file.close()
            self.mangaList = []
        elif filename.endswith(".json"):
            with open(filename) as json_file:
                self.mangaList = json.load(json_file)
                self.mangaDF = pd.DataFrame(self.mangaList)

    def get_manga_hosts(self):
        """
        Functionality: Will go through each line and parse for the host name while cutting it out and storing it into
        our dict list
        :param: None
        :return: None
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
        :param: None
        :return: None
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
        :param: None
        :return: None
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
        :param: None
        :return: None
        """
        for index, line in enumerate(self.fileInfo):
            self.mangaList[index]["Title"] = re.sub("\t|\n", "", line)

    def add_final_fields(self):
        """
        Functionality: This function is for adding the last fields that don't require any parsing of the original file
        contexts.
        :param: None
        :return: None
        """
        for manga in self.mangaList:
            manga["Kitsu ID"] = None
            manga["Manga Type"] = None
            manga["Ignore"] = False
            manga["Checked Date"] = None

    def update_with_new_fields(self, new_field):
        """
        Funcationality: Will go through our current list of mangas from self.mangaList and add this new key to each of
        them
        :param: new_field: A string to identify a new key to be added to our dict.
        :return: Nothing
        """
        for manga in self.mangaList:
            if new_field not in manga:
                manga[new_field] = None

    def get_manga_info(self):
        """
        Functionality: Simple function to excute all the required functions in the right order to get a complete list
        then put into a DataFrame.
        :param: None
        :return: None
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
        :param: None
        :return: None
        """
        self.mangaDF = pd.DataFrame(self.mangaList)

    def drop_duplicates(self):
        """
        Functionality: Drops duplicates from both mangaList and mangaDF.
        :param: None
        :return: None
        """
        self.mangaDF = pd.DataFrame(self.mangaList)
        self.mangaDF.drop_duplicates(keep="first", inplace=True)
        self.mangaList = self.mangaDF.to_dict(orient="records")

    def find_duplicate_ids(self):
        """
        Functionality: This function will find any IDs in our dataFrame that is a duplicate. This will be used for
        identifying issues where mangas with similar names have the same Kitsu ID.
        :param: None
        :return:
        """
        potentialIssues = self.mangaDF[self.mangaDF["Kitsu ID"].duplicated(keep=False)]
        potentialIssues = potentialIssues.loc[potentialIssues["Kitsu ID"].isna() == False]

        return potentialIssues

    def write_to_json(self, filename):
        """
        Functionality: This function is for writing a new json file with all the new opening filepath information as
        well as the old ones.
        :param filename: This parameter requires the user to give a name for the file to be created/updated
        :return: None
        """
        self.drop_duplicates()
        with open(filename, "w") as jsonFile:
            jsonFile.seek(0)
            json.dump(self.mangaList, jsonFile, indent=4, ensure_ascii=False)
            jsonFile.truncate()
            print(filename + " has been updated/created.")


class MangaComparer:
    def __init__(self, newMangaList, oldMangaList):
        """
        Functionality: This is to create the object with our new and old mangaList/mangaDF.
        :param newMangaList: This mangaList is a list of dicts containing Manga Information. This is typically the
        variable mangaList from the MangaListExtractor object.
        :param oldMangaList: This mangaList is a list of dicts containing Manga Information. This is typically the
        variable mangaList from the MangaListExtractor object.
        :return: None
        """
        self.oldList = oldMangaList.mangaDF
        self.newList = newMangaList.mangaDF
        self.newList = self.newList.merge(self.oldList, how="left", on=["Title"]).drop(["Kitsu ID_x", "Ignore_x",
                                                                                        "Host_y", "Status_y",
                                                                                        "Manga Link_y", "Manga Type_x",
                                                                                        "Checked Date_x"],
                                                                                       axis=1)
        self.newList = self.newList.rename(index=str, columns={"Host_x": "Host",
                                                               "Status_x": "Status",
                                                               "Manga Link_x": "Manga Link",
                                                               "Kitsu ID_y": "Kitsu ID",
                                                               "Manga Type_y": "Manga Type",
                                                               "Ignore_y": "Ignore",
                                                               "Checked Date_y": "Checked Date"})
        self.newList = self.newList.where(pd.notnull(self.newList), None)
        self.newList["Ignore"].fillna(value=False, inplace=True)

    def find_differences(self):
        """
        Functionality: This function will find the titles that were not found in the old list from the new list.
        :param: None
        :return: None
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
        Funcationality: This will log in to the user's Kitsu account and grab all the necessary information to be used
        later on like the access token. As well as intializing all necessary variables for error collecting.
        :param username: A string that is the Username used for Kitsu to log in.
        :param password: A string that is the Password used for Kitsu to log in.
        :return: None
        """
        self.KitsuMangaList = []
        self.JSONMangaList = Manager().list()
        self.counter = Manager().list()
        self.url = "https://kitsu.io/api"
        getTokenurl = "/oauth/token?grant_type=password&username=<username>&password=<password>"
        getTokenurl = getTokenurl.replace("<username>", username)
        getTokenurl = getTokenurl.replace("<password>", password)
        jsonInfo = requests.post(self.url + getTokenurl).json()
        self.access_token = jsonInfo["access_token"]
        self.token_type = jsonInfo["token_type"]
        self.header = {"Authorization": self.token_type + ' ' + self.access_token, "Content-Type": "application/vnd.api+json"}
        self.user_id = requests.get(self.url + "/edge/users?filter[self]=true",
                                    headers=self.header).json()["data"][0]["id"]
        self.errors = Manager().list()
        self.updatedTitles = Manager().list()

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
        :param: None
        :return: None
        """
        mangas = requests.get(self.url + "/edge/library-entries?filter[kind]=manga&filter[user_id]="
                              + self.user_id + "&fields[libraryEntries]=id" + "&include=manga"
                              + "&fields[manga]=titles,status,mangaType" + "&page[limit]=500", headers=self.header).json()
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
        Functionality: Uses the manga title to retrieve information regarding that manga but this will result in a list
        of potential titles that match it.
        :param title: The title of the manga series.
        :return: A list of dicts with a bunch of potential results matching that manga series.
        """
        result = requests.get("https://kitsu.io/api/edge/manga?filter[text]=" + title.replace(" ", "+")).json()
        return result

    def get_manga_id(self, index, manga):
        """
        Functionality: Goes through all the potential results the Kitsu website gives us after looking it up and doing
        its best to match it with the exact result.
        :param index: Index is an int variable that is used within our list to keep track of the order of the manga
        within list to be used later. When passing index make sure it corresponds with the index number of the manga
        that was passed in. It won't mess anything up but its more of a reference thing for the programmer to see
        what title went wrong.
        :param manga: This is a dict that contains information of our manga from the file it was retrieved from.
        :return: None
        """
        if (manga["Kitsu ID"] is None) and (manga["Ignore"] is False):
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
                                                               "Kitsu ID": result["data"][0]["id"],
                                                               "Manga Type": result["data"][0]["attributes"]["mangaType"]})
                                    matched = True
                                    break

                        if matched is False:
                            if result["data"][0]["attributes"]["abbreviatedTitles"]:
                                for AB_title in result["data"][0]["attributes"]["abbreviatedTitles"]:
                                    if AB_title is not None:
                                        if AB_title.lower() == manga["Title"].lower():
                                            logging.debug("Index: " + str(index) + " " + manga["Title"] + " ID: " + result["data"][0]["id"])
                                            self.JSONMangaList.append({"Index": index, "Title": manga["Title"],
                                                                       "Kitsu ID": result["data"][0]["id"],
                                                                       "Manga Type": result["data"][0]["attributes"]["mangaType"]})
                                            matched = True

                            if matched is False:
                                logging.debug("Index: " + str(index) + " " + manga["Title"] + " ID: " + "N/A")
                                self.JSONMangaList.append({"Index": index, "Title": manga["Title"],
                                                           "Kitsu ID": None,
                                                           "Manga Type": None})
                else:
                    logging.debug("Index: " + str(index) + " " + manga["Title"] + " ID: " + "N/A")
                    self.JSONMangaList.append({"Index": index, "Title": manga["Title"],
                                               "Kitsu ID": None,
                                               "Manga Type": None})

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
        Functionality: This will use the multiprocessing based on however many cores the user has. It will take the
        mangaList is recieved and split it up among the processes and retrieve all the information it can get.
        :param mangaList: Takes a list of dicts of manga. This should typically be from the MangaExtractor.mangaList
        :return: None
        """
        with Pool(os.cpu_count()) as p:
            p.starmap(self.get_manga_id, enumerate(mangaList))
        print("Manga's Finished Processing: {}".format(len(self.JSONMangaList)))

    def update_list(self, mangaList):
        """
        Funcationality: Goes through the list of manga it recieved and updates it with the list of manga ids we got.
        :param mangaList: Takes a list of dicts of manga. This should typically be from the MangaExtractor.mangaList
        :return: Returns that same list back for the user to manipulate later.
        :return mangaList: A list of dicts containing manga information that the user passed in that is now updated with
        new infomration.
        :return updatedManga: A list of dicts containing manga information of mangas that got updated.
        """
        updatedManga = []
        for manga in self.JSONMangaList:
            if ((manga["Kitsu ID"] is not None) and (mangaList[manga["Index"]]["Title"] == manga["Title"]) and
               (mangaList[manga["Index"]]["Kitsu ID"] is None)):
                mangaList[manga["Index"]]["Kitsu ID"] = manga["Kitsu ID"]
                mangaList[manga["Index"]]["Manga Type"] = manga["Manga Type"]
                logging.debug("Updated {}, Index: {}".format(manga["Title"], manga["Index"]))
                updatedManga.append(mangaList[manga["Index"]])
        print("Number of Manga IDs Updated: {}".format(len(updatedManga)))

        return mangaList, updatedManga

    def find_dropped_manga(self, mangaList, referencefile):
        """
        Functionality: This function will pull all the mangas from the user's Kitsu profile that was not found in the
        user's json file they passed in. This will in turn give a list of potential mangas that should be considered as
        dropped by the user. It is advise to go through the list of not_found_mangas and make sure the information is
        correct before calling the drop_update_kitsu_library to update user's Kitsu library with dropped series.
        :param mangaList: A list of dicts containing manga information. This is typically the variable mangaList from
        the MangaExtractorUpdate object,
        :param referencefile: A list of dicts containing manga information of dropped series. This is an optional
        parameter. This is used to cross reference any previous not_found_mangas*.json file that was created from this
        function. It will merge the two.
        :return: A list of dicts containing mangas that were not found in the list of mangas the user provided but was
        found on the user's Kitsu account.
        """
        self.get_current_library_entries()
        not_found_mangas = []
        for index, kitsu_manga in enumerate(self.KitsuMangaList):
            titles = list(filter(None, list(kitsu_manga["attributes"]["titles"].values())))
            if not any(manga["Kitsu ID"] == kitsu_manga["id"] for manga in mangaList):
                not_found_mangas.append({"Title": titles[0],
                                         "ID": kitsu_manga["id"],
                                         "Manga Type": kitsu_manga["attributes"]["mangaType"],
                                         "Ignore": False})
                logging.debug("==========================================================")
                logging.debug("Manga Not Found in list from Kitsu: {}".format(titles[0]))
                logging.debug("Index: {}".format(index))
                logging.debug("Manga ID: {}".format(kitsu_manga["id"]))
                logging.debug("Manga Type: {}".format(kitsu_manga["attributes"]["mangaType"]))
                logging.debug("==========================================================")
            else:
                logging.debug("==========================================================")
                logging.debug("Manga in list from Kitsu: {}".format(titles[0]))
                logging.debug("Index: {}".format(index))
                logging.debug("Manga ID: {}".format(kitsu_manga["id"]))
                logging.debug("Manga Type: {}".format(kitsu_manga["attributes"]["mangaType"]))
                logging.debug("==========================================================")

        if referencefile:
            logging.debug("Merging reference file with list of mangas not found...")
            with open(referencefile) as ref_file:
                ref_list = json.load(ref_file)

            for ref_index, ref_manga in enumerate(ref_list):
                for nf_index, nf_manga in enumerate(not_found_mangas):
                    if ref_manga["ID"] == nf_manga["ID"]:
                        nf_manga["Ignore"] = ref_manga["Ignore"]

        print("Number of not found manga from Kitsu in list: {}".format(len(not_found_mangas)))
        return not_found_mangas

    def update_kitsu_library_entry(self, index, manga):
        """
        Functionality: Updates Kitsu website with the manga information of its current status based on the Kitsu ID
        that is set.
        :param index: An int variable. Serves no current purpose due to how the multiprocessing function
        update_kitsu_library is set up.
        :param manga: This is a dict that contains information of our manga from the file it was retrieved from.
        :return: None
        """
        post_data = {
            'data': {
                'type': 'library-entries',
                'attributes': {
                    'status': None
                },
                'relationships': {
                    'user': {
                        'data': {
                            'type': 'users',
                            'id': self.user_id
                        }
                    },
                    'manga': {
                        'data': {
                            'type': 'manga',
                            'id': None
                        }
                    }
                }
            }
        }
        patch_data = {
            "data": {
                "type": "libraryEntries",
                "id": None,
                "attributes": {
                    "status": None
                }
            }
        }

        self.counter.append("1")
        if manga["Kitsu ID"] is not None:
            geturl = "https://kitsu.io/api/edge/library-entries?filter[user_id]={}&filter[manga_id]={}" \
                     "".format(self.user_id, manga["Kitsu ID"])
            jsonInfo = requests.get(geturl, headers=self.header).json()

            if not jsonInfo["data"]:
                posturl = "https://kitsu.io/api/edge/library-entries"
                post_data["data"]["attributes"]["status"] = manga["Status"]
                post_data["data"]["relationships"]["manga"]["data"]["id"] = manga["Kitsu ID"]
                response = requests.post(posturl, json=post_data, headers=self.header)
                statusCode = response.status_code

                if 200 <= statusCode < 300:
                    logging.debug("{} was updated on Kitsu. Status Code: {}".format(manga["Title"], statusCode))
                    self.updatedTitles.append({"Manga Title": manga["Title"],
                                               "Kitsu ID": manga["Kitsu ID"],
                                               "Status": manga["Status"],
                                               "Type": "POST",
                                               "Status Code": response.status_code,
                                               "Response": response})
                else:
                    logging.debug("{} was not updated. Error code: {}".format(manga["Title"], statusCode))
                    self.errors.append({"Manga Title": manga["Title"],
                                        "Kitsu ID": manga["Kitsu ID"],
                                        "Status Code": response.status_code,
                                        "Response": response})
            else:
                if jsonInfo["data"][0]["attributes"]["status"] != manga["Status"]:
                    libray_entry_id = jsonInfo["data"][0]["id"]
                    patchurl = "https://kitsu.io/api/edge/library-entries/{}".format(libray_entry_id)
                    patch_data["data"]["id"] = libray_entry_id
                    patch_data["data"]["attributes"]["status"] = manga["Status"]
                    response = requests.patch(patchurl, json=patch_data, headers=self.header)
                    statusCode = response.status_code

                    if 200 <= statusCode < 300:
                        logging.debug("{} was updated on Kitsu. Status Code: {}".format(manga["Title"], statusCode))
                        self.updatedTitles.append({"Manga Title": manga["Title"],
                                                   "Kitsu ID": manga["Kitsu ID"],
                                                   "Status": manga["Status"],
                                                   "Type": "PATCH",
                                                   "Status Code": response.status_code,
                                                   "Response": response})
                    else:
                        logging.debug("{} was not updated. Error code: {}".format(manga["Title"], statusCode))
                        self.errors.append({"Manga Title": manga["Title"],
                                            "Kitsu ID": manga["Kitsu ID"],
                                            "Status Code": response.status_code,
                                            "Response": response})
                else:
                    logging.debug("{} was not updated. No new status update".format(manga["Title"]))
        else:
            logging.debug("{} was not updated. No Kitsu ID".format(manga["Title"]))

        print("Manga's Finished Processing: {}".format(len(self.counter)), end="\r")

    def update_kitsu_library(self, mangaList):
        """
        Functionality: Will go through the list of mangas and use multiprocessing to update multiple manga titles at
        once
        :param mangaList: Takes a list of dicts of manga. This should typically be from the MangaExtractor.mangaList
        :return: None
        """
        with Pool(os.cpu_count()) as p:
            p.starmap(self.update_kitsu_library_entry, enumerate(mangaList))
        print("Manga's Finished Processing: {}".format(len(self.counter)))
        print("Manga Errors: {}".format(len(self.errors)))
        print("Mangas Updated: {}".format(len(self.updatedTitles)))
        self.counter = Manager().list()
        print("\n")

    def drop_update_kitsu_library(self, mangaList):
        """
        Functionality: Will go through the list of mangas and update all mangas that need to be dropped.
        :param mangaList: Takes a list of dicts of manga. This should typically be from json not_found_manga*.json file
        :return: None
        """
        patch_data = {
            "data": {
                "type": "libraryEntries",
                "id": None,
                "attributes": {
                    "status": None
                }
            }
        }
        for manga in mangaList:
            if manga["Ignore"] is False:
                geturl = "https://kitsu.io/api/edge/library-entries?filter[user_id]={}&filter[manga_id]={}" \
                         "".format(self.user_id, manga["ID"])
                jsonInfo = requests.get(geturl, headers=self.header).json()

                if jsonInfo["data"][0]["attributes"]["status"] != "dropped":
                    libray_entry_id = jsonInfo["data"][0]["id"]
                    patchurl = "https://kitsu.io/api/edge/library-entries/{}".format(libray_entry_id)
                    patch_data["data"]["id"] = libray_entry_id
                    patch_data["data"]["attributes"]["status"] = "dropped"
                    response = requests.patch(patchurl, json=patch_data, headers=self.header)
                    statusCode = response.status_code

                    if 200 <= statusCode < 300:
                        print("{} was updated on Kitsu. Status Code: {}".format(manga["Title"], statusCode))
                        self.successes.append({"Manga Title": manga["Title"],
                                               "Kitsu ID": manga["ID"],
                                               "Status": "dropped",
                                               "Type": "PATCH",
                                               "Status Code": response.status_code,
                                               "Response": response})
                    else:
                        print("{} was not updated. Error code: {}".format(manga["Title"], statusCode))
                        self.errors.append({"Manga Title": manga["Title"],
                                            "Kitsu ID": manga["Kitsu ID"],
                                            "Status Code": response.status_code,
                                            "Response": response})

    def write_to_json(self, filename, mangaList):
        """
        Functionality: This function is for creating/updating a JSON files with a list of dicts that was passed in.
        :param filename: This parameter requires the user to give a name for the file to be created/updated
        :param mangaList: This parameter requires the user to give a list of manga titles to append to our JSON file
        :return: None
        """
        with open(filename, "w") as jsonFile:
            jsonFile.seek(0)
            json.dump(mangaList, jsonFile, indent=4, ensure_ascii=False)
            jsonFile.truncate()
            print(filename + " has been updated/created.")


class MenuOption():
    def __init__(self):
        """
        Functionality: Initializes the object username and password.
        :param: None
        :return: None
        """
        self.username = None
        self.password = None
        self.KitsuErrors = []

    def check_input(self, listofitems, user_input):
        """
        Functionality: It will determine if the user entered an index or an actual string and return accordingly.
        :param listofitems: A list containing whatever the user if want to retrieve something from.
        :param user_input: The string of a user's input.
        :return: An item from the list that was provided based on index or just the string itself.
        """
        if user_input.isnumeric():
            return listofitems[int(user_input)]
        else:
            return user_input

    def print_logo(self):
        """
        Functionality: Simple function for printing the logo.
        :param: None
        :return: None
        """
        os.system("cls" if os.name == "nt" else "clear")
        print("""
        ********************************************************************************************************************
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        ********************************************************************************************************************
                __  ___                           __    _      __                                 
               /  |/  /___ _____  ____ _____ _   / /   (_)____/ /_                                
              / /|_/ / __ `/ __ \/ __ `/ __ `/  / /   / / ___/ __/                                
             / /  / / /_/ / / / / /_/ / /_/ /  / /___/ (__  ) /_                                  
            /_/  /_/\__,_/_/ /_/\__, /\__,_/  /_____/_/____/\__/                                  
               __  __          //___/  __          ________     __                  __            
              / / / /___  ____/ /___ _/ /____    _/_/ ____/  __/ /__________ ______/ /_____  _____
             / / / / __ \/ __  / __ `/ __/ _ \ _/_// __/ | |/_/ __/ ___/ __ `/ ___/ __/ __ \/ ___/
            / /_/ / /_/ / /_/ / /_/ / /_/  __//_/ / /____>  </ /_/ /  / /_/ / /__/ /_/ /_/ / /    
            \____/ .___/\__,_/\__,_/\__/\___/_/  /_____/_/|_|\__/_/   \__,_/\___/\__/\____/_/     
            /_/  
        ********************************************************************************************************************
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        ********************************************************************************************************************                                                                             
         """)

    def print_bars(self):
        """
        Functionality: Prints a bar for terminal formatting.
        :param: None
        :return: None
        """
        print("=======================================================================================================")

    def print_options_one(self):
        """
        Functionality: Prints the first set of menu options.
        :param: None
        :return: None
        """
        print("List Of Options")
        self.print_bars()
        print("1. Extract manga information from a .msbf file")
        print("2. Update Manga List with another existing Manga List")
        print("3. Auto find all Manga IDs")
        print("4. Find dropped series")
        print("5. Find Manga IDs")
        print("6. Find issues with manga list")
        print("7. Update Kitsu Website with dropped manga with JSON file")
        print("8. Update Kitsu Website with a JSON File")
        print("9. Exit")
        self.print_bars()

    def print_options_two(self, problemType):
        """
        Functionality: Prints the second set of menu options. This set of menu is for deciding what to do with the
        passed in problem type.
        :param problemType: This is a string identifying what kind of problem type the user wants to use the menu for.
        So far there's only two option which is Missing IDs and Duplicate IDs.
        :return: None
        """
        print("List Of Options")
        self.print_bars()
        print("1. Look up manga ID on Kitsu")
        print("2. Manually update a manga's information")
        if problemType == "Missing IDs":
            print("3. Go through all Manga's without IDs and look for the best match")
            print("4. Display mangas without IDs")
        elif problemType == "Duplicate IDs":
            print("3. Go through all Manga's with duplicate IDs and look for the best match")
            print("4. Display mangas with duplicate IDs")
        print("5. Display all mangas")
        print("6. Toggle search mode")
        print("7. Return to previous menu")
        self.print_bars()

    def print_options_three(self):
        """
        Functionality: Prints the third set of menu options. These are the options for when iterating through mangas and
        need to make changes.
        :param: None
        :return: None
        """
        print("What would you like to do?\n"
              "1. Update with one of the results from above\n"
              "2. Proceed to next manga in list\n"
              "3. Go back to previous manga in list\n"
              "4. Search manga with different title\n"
              "5. Reset current manga back to original settings\n"
              "6. Mark manga as ignore \n"
              "7. Go to different index number of manga counter\n"
              "8. Save all changes\n"
              "9. Discard all changes \n"
              "10. Exit back to previous menu option\n"
              "11. Exit to main menu\n")
        print("---------------------------------------------------------------------------------------")

    def print_manga_info(self, manga):
        """
        Functionality: This function will print out the current manga's information which include all key values in a
        pretty formatted statement.
        :param manga: This is a dict which contains manga information.
        :return: None
        """
        self.print_bars()
        print("Host: {}\n"
              "Ignore: {}\n"
              "Kitsu ID: {}\n"
              "Manga Link: {}\n"
              "Manga Type: {}\n"
              "Status: {}\n"
              "Checked Date: {}\n"
              "Title: {}".format(manga["Host"],
                                 manga["Ignore"],
                                 manga["Kitsu ID"],
                                 manga["Manga Link"],
                                 manga["Manga Type"],
                                 manga["Status"],
                                 manga["Checked Date"],
                                 manga["Title"]))
        self.print_bars()

    def update_manga_field(self, jsonmangaList, filename):
        """
        Functionality: This function will update whichever specific dict which is a manga in our list. It will update
        whichever key value and then save it back to the filename.
        :param jsonmangaList: A list of dicts where the dicts are manga information.
        :param filename: A string containing the name of the filename.
        :return: None
        """
        mangaInfo = int(input("Please enter index number of manga from list: "))
        mangaFields = ["Host", "Ignore", "Title", "Kitsu ID", "Manga Link", "Manga Type", "Status",
                       "Checked Date"]
        while True:
            self.print_manga_info(jsonmangaList.mangaList[mangaInfo])
            field_input = input("Please enter which field you plan to update "
                                "(to update another manga type exit): ")
            if field_input.lower() == "exit":
                print("\n")
                break
            elif field_input not in mangaFields:
                print("Invalid Field")
            else:
                value_input = input("Please enter new value for field: ")
                if value_input == "True":
                    jsonmangaList.mangaList[mangaInfo][field_input] = True
                elif value_input == "False":
                    jsonmangaList.mangaList[mangaInfo][field_input] = False
                elif value_input.lower() == "none" or value_input.lower() == "null":
                    jsonmangaList.mangaList[mangaInfo][field_input] = None
                else:
                    jsonmangaList.mangaList[mangaInfo][field_input] = value_input
        jsonmangaList.write_to_json(filename)

    def list_files(self, fileExtension):
        """
        Functionality: This function will list all the files found in the directory in alphabetical order.
        :param fileExtension: A string with the file extension name that we only want to list.
        :return: None
        """
        files = []
        print("\n{} files".format(fileExtension))
        self.print_bars()
        filesInDir = os.listdir()
        filesInDir.sort()
        for file in filesInDir:
            if file.endswith(fileExtension):
                print("{}. {}".format(str(len(files)), file))
                files.append(file)
        self.print_bars()

        return files

    def ExecuteMenu(self):
        """
        Functionality: This function is where it executes a bunch of different menu options that will walk the user
        through a bunch of different prompts while doing a bunch of different things according to the menu option.
        :param: None
        :return: None
        """
        self.username = input("Please enter Kitsu username: ")
        self.password = getpass.getpass(prompt="Please enter Kitsu password: ")
        test_login = Kitsu(self.username,
                           self.password) # Won't be using for anything besides testing if the username/password is valid
        self.print_logo()
        print("Welcome to the MangaStorm to Kitsu Updater/Exactor")
        while True:
            self.print_options_one()
            user_input = input("Please enter option: ")

            if user_input == "1":
                files = self.list_files(".msbf")
                msbffile = self.check_input(files, input("Please select option or enter name: "))
                mangaListExtraction = MangaListExtractor(msbffile)
                mangaListExtraction.get_manga_info()

                filename = input("Please enter a name to save the file as (do not add extension name like .json): ")
                mangaListExtraction.write_to_json((filename + "-" + str(datetime.datetime.now().date()) + ".json"))
                print("\n")

            elif user_input == "2":
                print("\n**********************************************************************************************"
                      "\nNote: This option works by requiring the user to have a pre-existing JSON file that has "
                      "\nManga IDs This will work by taking a old JSON file and taking all the IDs that it should "
                      "\nalready have and merge it with our new JSON file that should have any IDs."
                      "\n**********************************************************************************************"
                      )
                files = self.list_files(".json")
                newfile = self.check_input(files, input("Please select option or enter name of "
                                                        "new .json file to update: "))
                oldfile = self.check_input(files, input("Please select option or enter name of "
                                                        "old .json file to with: "))

                newList = MangaListExtractor(newfile)
                oldList = MangaListExtractor(oldfile)
                comparer = MangaComparer(newList, oldList)
                newList.mangaList = comparer.newList.to_dict(orient="records")
                newList.write_to_json(newfile)
                print("\n")

            elif user_input == "3":
                files = self.list_files(".json")
                jsonfile = self.check_input(files, input("Please select option or enter name of "
                                                         ".json file to update: "))
                jsonmangaList = MangaListExtractor(jsonfile)
                KitsuUpdater = Kitsu(self.username, self.password)
                KitsuUpdater.get_manga_ids(jsonmangaList.mangaList)
                jsonmangaList.mangaList, updatedManga = KitsuUpdater.update_list(jsonmangaList.mangaList)
                jsonmangaList.update_df()
                updatedManga = pd.DataFrame(updatedManga)
                self.print_bars()
                print("Updated Entries")
                self.print_bars()
                print(updatedManga[["Title", "Status", "Kitsu ID"]])

                while True:
                    user_input = input("Would you like to save results? (Y/N): ")
                    if user_input.lower() == "y" or user_input.lower() == "yes":
                        jsonmangaList.write_to_json(jsonfile)
                        break
                    elif user_input.lower() == "n" or user_input.lower() == "no":
                        print("{} was not updated.".format(jsonfile))
                        break
                    else:
                        print("Invalid input, please try again.")
                print("\n")

            elif user_input == "4":
                print("\n**********************************************************************************************"
                      "\nNote: This options is for compiling a list of Mangas that was found on Kitsu but not found in"
                      "\nthe specified JSON fille. The use of this is to later update the Kitsu Website with series"
                      "\nthat was dropped by the user. It's also used for the user to double check their new JSON list"
                      "\nand cross reference if the manga titles and IDs are correct with the ones found by the "
                      "\nprogram. This can be seen with the program finding manga IDs for some series but putting the "
                      "\nwrong ID due to it taking the ID of a oneshot and not the actual running manga. This could've"
                      "\nbeen avoided but MangaStorm doesn't include that in their file. Also, it will compare"
                      "\nnot_found_manga.json files to skip series that shouldn't be dropped."
                      "\n**********************************************************************************************"
                      )
                files = self.list_files(".json")
                jsonfile = self.check_input(files, input("Please select option or enter the name of new .json file to "
                                                         "compare with the mangas found on Kitsu: "))
                jsonmangaList = MangaListExtractor(jsonfile)
                KitsuUpdater = Kitsu(self.username, self.password)

                user_input = input("Would you like to use a previous not_found_manga*.jso"
                                   "file as a reference? (Y/N): ")
                while True:
                    if user_input.lower() == "y" or user_input.lower() == "yes":
                        referencefile = self.check_input(files, input("Please select option or enter name of "
                                                                      "not_found_manga*.json file to be used for reference:"
                                                                      " "))
                        mangaList = KitsuUpdater.find_dropped_manga(jsonmangaList.mangaList, referencefile)
                        break
                    elif user_input.lower() == "n" or user_input.lower() == "no":
                        mangaList = KitsuUpdater.find_dropped_manga(jsonmangaList.mangaList, None)
                        break
                    else:
                        print("Invalid input, please try again")

                user_input = input("\nWould you like to save not found mangas in JSON file? (Y/N): ")
                if user_input.lower() == "y" or user_input.lower() == "yes":
                    KitsuUpdater.write_to_json(
                        ("not_found_mangas" + "-" + str(datetime.datetime.now().date()) + ".json"),
                        mangaList)
                else:
                    print("Did not save results...\n")

            elif user_input == "5":
                files = self.list_files(".json")
                jsonfile = self.check_input(files, input("Please select option or enter the name of new .json file "
                                                         "to find Manga IDs for: "))

                jsonmangaList = MangaListExtractor(jsonfile)
                jsonmangaListBackUp = MangaListExtractor(jsonfile)
                KitsuUpdater = Kitsu(self.username, self.password)
                problemIDs = jsonmangaList.mangaDF.loc[(jsonmangaList.mangaDF["Kitsu ID"].isna()) &
                                                       (jsonmangaList.mangaDF["Kitsu ID"].isna())]
                problemType = "Missing IDs"
                self.ExecuteMenuTwo(jsonfile, jsonmangaList, jsonmangaListBackUp, KitsuUpdater, problemIDs, problemType)

            elif user_input == "6":
                files = self.list_files(".json")
                jsonfile = self.check_input(files, input("Please select option or enter the name of new .json file "
                                                         "to find issues for: "))

                jsonmangaList = MangaListExtractor(jsonfile)
                jsonmangaListBackUp = MangaListExtractor(jsonfile)
                KitsuUpdater = Kitsu(self.username, self.password)
                problemIDs = jsonmangaList.find_duplicate_ids()
                problemType = "Duplicate IDs"
                self.ExecuteMenuTwo(jsonfile, jsonmangaList, jsonmangaListBackUp, KitsuUpdater, problemIDs, problemType)

            elif user_input == "7":
                files = self.list_files(".json")
                jsonfile = self.check_input(files, input("Please select option or enter the name of not_found_mangas* "
                                                         ".json file to be used for updating the Kitsu website with: "))
                jsonmangaList = MangaListExtractor(jsonfile)
                KitsuUpdater = Kitsu(self.username, self.password)
                KitsuUpdater.drop_update_kitsu_library(jsonmangaList.mangaList)
                self.KitsuErrors = KitsuUpdater.errors

            elif user_input == "8":
                files = self.list_files(".json")
                jsonfile = self.check_input(files, input("Please select option or enter the name of new .json file "
                                                    "to be used for updating the Kitsu website with: "))
                jsonmangaList = MangaListExtractor(jsonfile)
                KitsuUpdater = Kitsu(self.username, self.password)
                KitsuUpdater.update_kitsu_library(jsonmangaList.mangaList)
                self.KitsuErrors = KitsuUpdater.errors

            elif user_input == "9":
                print("Exiting program...\n")
                break
            else:
                print("Invalid input\n")

    def ExecuteMenuTwo(self, jsonfile, jsonmangaList, jsonmangaListBackUp, KitsuUpdater, problemIDs, problemType):
        """
        Functionality: This function will execute the second set and third set of menu options to update the json file.
        :param jsonfile: A string with the name of a json file.
        :param jsonmangaList: A list of dicts where the dicts are manga information.
        :param jsonmangaListBackUp: A backup list of dicts where the dicts are manga information.
        :param KitsuUpdater: A Kitsu object.
        :param problemIDs: A list of dicts where the dicts are manga information. But this list is specific with only
        mangas that had duplicate IDs found in the jsonmangaList.
        :param problemType: A string specificing the problem type which could "Missing IDs" or "Duplicate IDs".
        :return: None
        """
        searchMode = False
        go_to_main_menu = False
        self.print_bars()
        print(problemIDs[["Title", "Host", "Kitsu ID", "Ignore", "Checked Date"]])
        self.print_bars()

        while True:
            if go_to_main_menu is True:
                print("Returning back to main menu...\n")
                break

            self.print_options_two(problemType)
            user_input = input("Please enter option: ")

            if user_input == "1":
                while True:
                    print("Note: You can type in the index of the manga found in the list for the program to \n"
                          "reference or simply type the name of whatever manga you want to look up. \n"
                          "Note: Will only display up to 10 matches if you look up specific title on Kitsu")
                    print("SEARCHMODE: {}".format(searchMode))
                    mangaTitle = self.check_input(jsonmangaList.mangaList, input("Please enter index number or name "
                                                                                 "(or type Exit to go back to previous "
                                                                                 "menu selection): "))
                    print("\n")

                    if isinstance(mangaTitle, dict):
                        results = KitsuUpdater.manga_search(mangaTitle["Title"])
                    else:
                        if mangaTitle.lower() == "exit":
                            print("Returning to previous menu selection")
                            break
                        else:
                            results = KitsuUpdater.manga_search(mangaTitle)

                    os.system("cls" if os.name == "nt" else "clear")
                    print("***************************************************************************************")
                    print("Results")
                    for result in results["data"]:
                        titles = [title for title in (list(result["attributes"]["titles"].values()))
                                  if title is not None]
                        print("***************************************************************************************")
                        print("Titles: {}".format(", ".join(titles)))
                        print("Kitsu ID: {}".format(result["id"]))
                        print("Manga Type: {}".format(result["attributes"]["mangaType"]))
                        print("Synopsis: {}".format(result["attributes"]["synopsis"]))
                        print("***************************************************************************************")
                    print("\n")

                    if searchMode is False:
                        break
            elif user_input == "2":
                self.update_manga_field(jsonmangaList, jsonfile)
                self.print_bars()
                print(problemIDs[["Title", "Host", "Kitsu ID", "Ignore", "Checked Date"]])
                self.print_bars()

            elif user_input == "3":
                go_to_previous_menu = False
                title_search = False
                new_title = None
                mangaCounter = 0
                while mangaCounter < len(problemIDs.index):
                    index = problemIDs.index[mangaCounter]
                    if go_to_main_menu is True:
                        break
                    elif go_to_previous_menu is True:
                        print("Returning back to previous menu...\n")
                        break
                    if title_search is True:
                        results = KitsuUpdater.manga_search(new_title)
                        title_search = False
                    else:
                        results = KitsuUpdater.manga_search(jsonmangaList.mangaList[index]["Title"])

                    os.system("cls" if os.name == "nt" else "clear")
                    print("***************************************************************************************")
                    print("Results")
                    print("***************************************************************************************")
                    for resultIndex, result in enumerate(results["data"]):
                        titles = [title for title in (list(result["attributes"]["titles"].values()))
                                  if title is not None]
                        print("xxxxxxxxxxxxxx")
                        print("Option {}".format(resultIndex))
                        print("xxxxxxxxxxxxxx")
                        print("Titles: {}".format(", ".join(titles)))
                        print("Kitsu ID: {}".format(result["id"]))
                        print("Manga Type: {}".format(result["attributes"]["mangaType"]))
                        print("Synopsis: {}".format(result["attributes"]["synopsis"]))
                        print(
                            "*******************************************"
                            "********************************************")
                    print("\n")
                    self.print_manga_info(jsonmangaList.mangaList[index])
                    print("Manga Counter: {}/{}\n".format(mangaCounter, (len(problemIDs) - 1)))
                    self.print_bars()

                    while True:
                        self.print_options_three()
                        user_input = input("Please enter option: ")

                        if user_input == "1":
                            while True:
                                user_input = input("Please enter the corresponding option number: ")
                                if user_input.isnumeric():
                                    if int(user_input) < len(results["data"]):
                                        jsonmangaList.mangaList[index]["Kitsu ID"] = \
                                            results["data"][int(user_input)]["id"]
                                        jsonmangaList.mangaList[index]["Manga Type"] = \
                                            results["data"][int(user_input)]["attributes"]["mangaType"]
                                        jsonmangaList.mangaList[index]["Checked Date"] = None

                                        self.print_bars()
                                        print("Manga Result that you picked")
                                        self.print_bars()

                                        titles = [title for title in
                                                  (list(results["data"][int(user_input)]["attributes"][
                                                            "titles"].values()))
                                                  if title is not None]
                                        print("Titles: {}".format(", ".join(titles)))
                                        print("Kitsu ID: {}".format(results["data"][int(user_input)]["id"]))
                                        print("Manga Type: {}".format(
                                            results["data"][int(user_input)]["attributes"]["mangaType"]))
                                        print("Synopsis: {}".format(
                                            results["data"][int(user_input)]["attributes"]["synopsis"]))

                                        self.print_bars()
                                        print("Manga Field Update")
                                        self.print_bars()

                                        self.print_manga_info(jsonmangaList.mangaList[index])
                                        self.print_bars()
                                        break
                                    else:
                                        print("The number you provided was not one of the options provided above, "
                                              "please try again.")
                                else:
                                    print("The option you provided was not a number corresponding to the option, "
                                          "please try again.")
                        elif user_input == "2":
                            mangaCounter = mangaCounter + 1
                            if jsonmangaList.mangaList[index]["Kitsu ID"] is None:
                                jsonmangaList.mangaList[index]["Checked Date"] = str(datetime.datetime.now().date())
                            break
                        elif user_input == "3":
                            if mangaCounter == 0:
                                self.print_bars()
                                print("You're already at 0, can't go any further back than that")
                                self.print_bars()
                            else:
                                mangaCounter = mangaCounter - 1
                                if jsonmangaList.mangaList[index]["Kitsu ID"] is None:
                                    jsonmangaList.mangaList[index]["Checked Date"] = str(datetime.datetime.now().date())
                                break
                        elif user_input == "4":
                            new_title = input("Enter a different title to search for: ")
                            title_search = True
                            break
                        elif user_input == "5":
                            updated = False
                            jsonmangaList.mangaList[index]["Kitsu ID"] = None
                            jsonmangaList.mangaList[index]["Manga Type"] = None
                            jsonmangaList.mangaList[index]["Checked Date"] = None
                            self.print_bars()

                            self.print_manga_info(jsonmangaList.mangaList[index])
                            self.print_bars()
                        elif user_input == "6":
                            jsonmangaList.mangaList[index]["Ignore"] = True
                            self.print_bars()
                            print("Manga Updated to be ignored")
                            self.print_manga_info(jsonmangaList.mangaList[index])
                            self.print_bars()
                        elif user_input == "7":
                            while True:
                                index_input = input("What index number do you want to jump to?: ")
                                if index_input.isnumeric():
                                    if int(index_input) < len(problemIDs.index):
                                        mangaCounter = int(index_input)
                                        break
                                    else:
                                        print("Index you entered was greater "
                                              "than the highest manga count: {},"
                                              "please try again.".format(len(problemIDs.index)))
                                else:
                                    print("Input you entered was not an integer, please try again.")
                            break
                        elif user_input == "8":
                            self.print_bars()
                            jsonmangaList.write_to_json(jsonfile)
                            self.print_bars()
                        elif user_input == "9":
                            self.print_bars()
                            jsonmangaListBackUp.write_to_json(jsonfile)
                            self.print_bars()
                        elif user_input == "10":
                            go_to_previous_menu = True
                            break
                        elif user_input == "11":
                            go_to_main_menu = True
                            break
                        else:
                            self.print_bars()
                            print("Invalid input")
                            self.print_bars()

                user_input = input("Would you like to save any unsaved changes? (Y/N): ")
                if user_input.lower() == "y" or user_input.lower() == "yes":
                    jsonmangaList.write_to_json(jsonfile)
                    self.print_bars()
                    print("Unsaved changes were saved")
                    self.print_bars()
                else:
                    self.print_bars()
                    print("Unsaved changes were not saved")
                    self.print_bars()
            elif user_input == "4":
                if problemType == "Missing IDs":
                    jsonmangaList.update_df()
                    problemIDs = jsonmangaList.mangaDF.loc[jsonmangaList.mangaDF["Kitsu ID"].isna()]
                elif problemType == "Duplicate IDs":
                    jsonmangaList.update_df()
                    problemIDs = jsonmangaList.find_duplicate_ids()

                self.print_bars()
                print(problemIDs[["Title", "Host", "Kitsu ID", "Ignore", "Checked Date"]])
                self.print_bars()
            elif user_input == "5":
                jsonmangaList.update_df()
                print(jsonmangaList.mangaDF[["Title", "Kitsu ID"]])
            elif user_input == "6":
                if searchMode is False:
                    searchMode = True
                    print("Search Mode has been toggle on. \n")
                else:
                    searchMode = False
                    print("Search Mode has been toggled off. \n")
            elif user_input == "7":
                print("Returning to previous menu selection\n")
                break
            else:
                print("Invalid input")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    pd.set_option("display.max_rows", None)
    menu = MenuOption()
    menu.ExecuteMenu()
    """
    # For Debugging purposes
    username = "Whatever"
    password = "Whatever"
    newList = MangaListExtractor("mangalist-2020-07-19.json")
    oldList = MangaListExtractor("mangalist-2020-06-11.json")
    newListKitsu = Kitsu(username, password)
    oldListKitsu = Kitsu(username, password)
    # newList.update_with_new_fields("Checked Date")
    # newList.update_df()
    # oldList.update_with_new_fields("Checked Date")
    # oldList.update_df()

    # newList.get_manga_info()
    # oldList.get_manga_info()

    # newListKitsu.get_manga_ids(newList.mangaList)
    # oldListKitsu.get_manga_ids(oldList.mangaList)

    # newList.mangaList = newListKitsu.update_list(newList.mangaList)
    # oldList.mangaList = oldListKitsu.update_list(oldList.mangaList)
    # newList.update_df()
    # oldList.update_df()

    # comparer = MangaComparer(newList, oldList)
    """

