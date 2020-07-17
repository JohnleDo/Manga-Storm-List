# TODO: Fix some print statements to be neater throughout the program
# TODO: Fix lines where it exceeds the character limit
# TODO: Have better naming scheme
# TODO: Use list comphrension for for loops
# TODO: Added a new field called check date, go through code and fix print statements to include this new field
# TODO: Make use of the check date field in the manga No ID searching interface, it will be used for easier
#  identification of series that have been already searched.
import pandas as pd
import re
import json
import requests
from multiprocessing import Pool, Manager
import datetime
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
            with open(filename) as json_file:
                self.mangaList = json.load(json_file)
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
            manga["Manga Type"] = None
            manga["Ignore"] = False
            manga["Checked Date"] = None

    def update_with_new_fields(self, new_field):
        """

        :return:
        """
        for manga in self.mangaList:
            if new_field not in manga:
                manga[new_field] = None

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
                mangaList[manga["Index"]]["Manga Type"] = manga["Manga Type"]
                logging.debug("Updated {}, Index: {}".format(manga["Title"], manga["Index"]))
                counter = counter + 1
        print("Number of Manga IDs Updated: " + str(counter))

        return mangaList

    def find_dropped_manga(self, mangaList, referencefile):
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

    def write_to_json(self, filename, mangaList):
        """
        :param filename: This parameter requires the user to give a name for the file to be created/updated
        :param mangaList: This parameter requires the user to give a list of manga titles to append to our JSON file
        Functionality: This function is for creating/updating a JSON files with a list of dicts that was passed in.
        """
        with open(filename, "w") as jsonFile:
            jsonFile.seek(0)
            json.dump(mangaList, jsonFile, indent=4, ensure_ascii=False)
            jsonFile.truncate()
            print(filename + " has been updated/created.")

    def request_test(self, something):
        self.test = requests.get(something).json()


def check_input(listofitems, user_input):
    """
    :param listofitems: A list containing whatever the user if want to retrieve something from.
    :param user_input: The string of a user's input.
    :return: An item from the list that was provided based on index or just the string itself.
    Functionality: It will determine if the user entered an index or an actual string and return accordingly.
    """
    if user_input.isnumeric():
        return listofitems[int(user_input)]
    else:
        return user_input


def menu_option():
    username = input("Please enter Kitsu username: ")
    password = input("Please enter Kitsu password: ")
    test_login = Kitsu(username, password) # Won't be using for anything besides testing if the username/password is valid
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
    print("Welcome to the MangaStorm to Kitsu Updater/Exactor")
    while True:
        print("List Of Options")
        print("=======================================================================================================")
        print("1. Extract manga information from a .msbf file")
        print("2. Update Manga List with another existing Manga List")
        print("3. Attempt to find and update all manga id in JSON file")
        print("4. Find dropped series")
        print("5. Update Manga Information or Search for Manga IDs")
        print("6. Update Kitsu Website with dropped manga with JSON file")
        print("7. Update Kitsu Website with JSON File")
        print("8. Exit")
        print("=======================================================================================================")

        user_input = input("Please enter option: ")

        if user_input == "1":
            files = []
            print("\nMSBF files")
            print("===================================================================================================")
            for file in os.listdir():
                if file.endswith(".msbf"):
                    print("{}. {}".format(str(len(files)), file))
                    files.append(file)
            print("===================================================================================================")
            msbffile = check_input(files, input("Please select option or enter name: "))

            mangaListExtraction = MangaListExtractor(msbffile)
            mangaListExtraction.get_manga_info()

            filename = input("Please enter a name to save the file as (do not add extension name like .json): ")
            mangaListExtraction.write_to_json((filename + "-" + str(datetime.datetime.now().date()) + ".json"))
            print("\n")

        elif user_input == "2":
            files = []
            print("\n*************************************************************************************************")
            print("Note: This option works by requiring the user to have a pre-existing JSON file that has Manga IDs")
            print("This will work by taking a old JSON file and taking all the IDs that it should already have and")
            print("merge it with our new JSON file that should have any IDs.")
            print("***************************************************************************************************")

            print("\nJSON Files")
            print("===================================================================================================")
            for file in os.listdir():
                if file.endswith(".json"):
                    print("{}. {}".format(str(len(files)), file))
                    files.append(file)
            print("===================================================================================================")
            newfile = check_input(files, input("Please select option or enter name of new .json file to update: "))
            oldfile = check_input(files, input("Please select option or enter name of old .json file to with: "))

            newList = MangaListExtractor(newfile)
            oldList = MangaListExtractor(oldfile)

            comparer = MangaComparer(newList, oldList)

            newList.mangaList = comparer.newList.to_dict(orient="records")
            newList.write_to_json(newfile)
            print("\n")

        elif user_input == "3":
            files = []
            print("\nJSON Files")
            print("=====================================================================")
            for file in os.listdir():
                if file.endswith(".json"):
                    print("{}. {}".format(str(len(files)), file))
                    files.append(file)
            print("=====================================================================")
            jsonfile = check_input(files, input("Please select option or enter name of .json file to update: "))

            jsonmangaList = MangaListExtractor(jsonfile)
            KitsuUpdater = Kitsu(username, password)
            KitsuUpdater.get_manga_ids(jsonmangaList.mangaList)
            jsonmangaList.mangaList = KitsuUpdater.update_list(jsonmangaList.mangaList)
            jsonmangaList.write_to_json(jsonfile)
            print("\n")

        elif user_input == "4":
            files = []
            print("\n*************************************************************************************************")
            print("Note: This options is for compiling a list of Mangas that was found on Kitsu but not found in the")
            print("specified JSON fille. The use of this is to later update the Kitsu Website with series that was")
            print("dropped by the user. It's also used for the user to double check their new JSON list and cross")
            print("reference if the manga titles and IDs are correct with the ones found by the program. This can be")
            print("seen with the program finding manga IDs for some series but putting the wrong ID due to it taking ")
            print("the ID of a oneshot and not the actual running manga. This could've been avoided but MangaStorm")
            print("doesn't include that in their file. Also, it will compare not_found_manga.json files to skip")
            print("series that shouldn't be dropped")
            print("***************************************************************************************************")

            print("\nJSON Files")
            print("===================================================================================================")
            for file in os.listdir():
                if file.endswith(".json"):
                    print("{}. {}".format(str(len(files)), file))
                    files.append(file)
            print("===================================================================================================")
            jsonfile = check_input(files, input("Please select option or enter the name of new .json file to compare "
                                                "with the mangas found on Kitsu: "))
            jsonmangaList = MangaListExtractor(jsonfile)
            KitsuUpdater = Kitsu(username, password)

            user_input = input("Would you like to use a previous not_found_manga*.json file as a reference? (Y/N): ")
            if user_input.lower() == "y" or user_input.lower() =="yes":
                referencefile = check_input(files, input("Please select option or enter name of not_found_manga*.json "
                                                         "file to be used for reference: "))
                mangaList = KitsuUpdater.find_dropped_manga(jsonmangaList.mangaList, referencefile)
            else:
                mangaList = KitsuUpdater.find_dropped_manga(jsonmangaList.mangaList)

            user_input = input("\nWould you like to save not found mangas in JSON file? (Y/N): ")
            if user_input.lower() == "y" or user_input.lower() =="yes":
                KitsuUpdater.write_to_json(("not_found_mangas" + "-" + str(datetime.datetime.now().date()) + ".json"),
                                           mangaList)

            else:
                print("Did not save results...\n")

        # TODO: This secion can be made better if I add the logo in the subsection, if so I need to make the logo a
        #  function of its own
        elif user_input == "5":
            searchMode = False
            files = []
            os.system("cls" if os.name == "nt" else "clear")
            print("\nJSON Files")
            print("===================================================================================================")
            filesInDir = os.listdir()
            filesInDir.sort()
            for file in filesInDir:
                if file.endswith(".json"):
                    print("{}. {}".format(str(len(files)), file))
                    files.append(file)
            print("===================================================================================================")
            jsonfile = check_input(files, input("Please select option or enter the name of new .json file "
                                                "to find Manga IDs for: "))

            jsonmangaList = MangaListExtractor(jsonfile)
            jsonmangaListBackUp = MangaListExtractor(jsonfile)
            KitsuUpdater = Kitsu(username, password)
            noIDs = jsonmangaList.mangaDF.loc[(jsonmangaList.mangaDF["Kitsu ID"].isna()) &
                                              (jsonmangaList.mangaDF["Kitsu ID"].isna())]
            print(noIDs)

            while True:
                print("List Of Options")
                print("===================================================="
                      "===================================================")
                print("1. Look up manga ID on Kitsu")
                print("2. Manually update a manga's information")
                print("3. Go through all Manga's without ID and look for the best match")
                print("4. Display mangas without ID")
                print("5. Display all mangas")
                print("6. Toggle search mode")
                print("7. Return to previous menu")
                print("===================================================="
                      "===================================================")

                user_input = input("Please enter option: ")

                if user_input == "1":
                    while True:
                        print("Note: You can type in the index of the manga found in the list for the program to \n"
                              "reference or simply type the name of whatever manga you want to look up. \n"
                              "Note: Will only display up to 10 matches if you look up specific title on Kitsu")
                        print("SEARCHMODE: {}".format(searchMode))
                        mangaTitle = check_input(jsonmangaList.mangaList, input("Please enter index number or name "
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
                    mangaInfo = int(input("Please enter index number of manga from list: "))
                    mangaFields = ["Host", "Ignore", "Title", "Kitsu ID", "Manga Link", "Manga Type", "Status",
                                   "Checked Date"]
                    while True:
                        print("Host: {}\n"
                              "Ignore: {}\n"
                              "Kitsu ID: {}\n"
                              "Manga Link: {}\n"
                              "Manga Type: {}\n"
                              "Status: {}\n"
                              "Checked Date: {}\n"
                              "Title: {}".format(jsonmangaList.mangaList[mangaInfo]["Host"],
                                                 jsonmangaList.mangaList[mangaInfo]["Ignore"],
                                                 jsonmangaList.mangaList[mangaInfo]["Kitsu ID"],
                                                 jsonmangaList.mangaList[mangaInfo]["Manga Link"],
                                                 jsonmangaList.mangaList[mangaInfo]["Manga Type"],
                                                 jsonmangaList.mangaList[mangaInfo]["Status"],
                                                 jsonmangaList.mangaList[mangaInfo]["Checked Date"],
                                                 jsonmangaList.mangaList[mangaInfo]["Title"]))
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
                            else:
                                jsonmangaList.mangaList[mangaInfo][field_input] = value_input
                elif user_input == "3":
                    go_back = False
                    title_search = False
                    new_title = None
                    mangaCounter = 0
                    while mangaCounter < len(noIDs.index):
                        index = noIDs.index[mangaCounter]
                        if go_back is True:
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
                        print("=======================================================================================")
                        print("Host: {}\n"
                              "Ignore: {}\n"
                              "Kitsu ID: {}\n"
                              "Manga Link: {}\n"
                              "Manga Type: {}\n"
                              "Status: {}\n"
                              "Checked Date: {}\n"
                              "Title: {}".format(jsonmangaList.mangaList[index]["Host"],
                                                 jsonmangaList.mangaList[index]["Ignore"],
                                                 jsonmangaList.mangaList[index]["Kitsu ID"],
                                                 jsonmangaList.mangaList[index]["Manga Link"],
                                                 jsonmangaList.mangaList[index]["Manga Type"],
                                                 jsonmangaList.mangaList[index]["Status"],
                                                 jsonmangaList.mangaList[index]["Checked Date"],
                                                 jsonmangaList.mangaList[index]["Title"]))
                        print("======================================"
                              "=================================================\n"
                              "Manga Counter: {}/{}\n"
                              "========================================"
                              "===============================================".format(mangaCounter, (len(noIDs) - 1)))
                        while True:
                            print("What would you like to do?\n"
                                  "1. Update with one of the results from above\n"
                                  "2. Proceed to next manga with no ID\n"
                                  "3. Search manga with different title\n"
                                  "4. Reset current manga back to original settings\n"
                                  "5. Mark manga as ignore \n"
                                  "6. Go to different index number of manga counter\n"
                                  "7. Save all changes\n"
                                  "8. Discard all changes \n"
                                  "9. Exit back to previous menu option\n"
                                  "10. Exit to main menu\n")
                            print("---------------------------------------------------------------------------------------")
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
                                            print("======================================"
                                                  "=================================================\n"
                                                  "Manga Result that you picked\n"
                                                  "=========================================="
                                                  "=============================================\n")
                                            titles = [title for title in
                                                      (list(results["data"][int(user_input)]["attributes"]["titles"].values()))
                                                      if title is not None]
                                            print("Titles: {}".format(", ".join(titles)))
                                            print("Kitsu ID: {}".format(results["data"][int(user_input)]["id"]))
                                            print("Manga Type: {}".format(results["data"][int(user_input)]["attributes"]["mangaType"]))
                                            print("Synopsis: {}".format(results["data"][int(user_input)]["attributes"]["synopsis"]))
                                            print("======================================"
                                                  "=================================================\n"
                                                  "Manga Field Update\n"
                                                  "=========================================="
                                                  "=============================================\n")
                                            print("Host: {}\n"
                                                  "Ignore: {}\n"
                                                  "Kitsu ID: {}\n"
                                                  "Manga Link: {}\n"
                                                  "Manga Type: {}\n"
                                                  "Status: {}\n"
                                                  "Checked Date: {}\n"
                                                  "Title: {}".format(jsonmangaList.mangaList[index]["Host"],
                                                                     jsonmangaList.mangaList[index]["Ignore"],
                                                                     jsonmangaList.mangaList[index]["Kitsu ID"],
                                                                     jsonmangaList.mangaList[index]["Manga Link"],
                                                                     jsonmangaList.mangaList[index]["Manga Type"],
                                                                     jsonmangaList.mangaList[index]["Status"],
                                                                     jsonmangaList.mangaList[index]["Checked Date"],
                                                                     jsonmangaList.mangaList[index]["Title"]))
                                            print(
                                                "==========================================="
                                                "============================================")
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
                                new_title = input("Enter a different title to search for: ")
                                title_search = True
                                break
                            elif user_input == "4":
                                updated = False
                                jsonmangaList.mangaList[index]["Kitsu ID"] = None
                                jsonmangaList.mangaList[index]["Manga Type"] = None
                                jsonmangaList.mangaList[index]["Checked Date"] = None
                                print(
                                    "==========================================="
                                    "============================================")
                                print("Host: {}\n"
                                      "Ignore: {}\n"
                                      "Kitsu ID: {}\n"
                                      "Manga Link: {}\n"
                                      "Manga Type: {}\n"
                                      "Status: {}\n"
                                      "Checked Date: {}\n"
                                      "Title: {}".format(jsonmangaList.mangaList[index]["Host"],
                                                         jsonmangaList.mangaList[index]["Ignore"],
                                                         jsonmangaList.mangaList[index]["Kitsu ID"],
                                                         jsonmangaList.mangaList[index]["Manga Link"],
                                                         jsonmangaList.mangaList[index]["Manga Type"],
                                                         jsonmangaList.mangaList[index]["Status"],
                                                         jsonmangaList.mangaList[index]["Checked Date"],
                                                         jsonmangaList.mangaList[index]["Title"]))
                                print(
                                    "==========================================="
                                    "============================================")
                            elif user_input == "5":
                                jsonmangaList.mangaList[index]["Ignore"] = True
                                print(
                                    "==========================================="
                                    "============================================")
                                print("Manga Updated to be ignored")
                                print("Host: {}\n"
                                      "Ignore: {}\n"
                                      "Kitsu ID: {}\n"
                                      "Manga Link: {}\n"
                                      "Manga Type: {}\n"
                                      "Status: {}\n"
                                      "Checked Date: {}\n"
                                      "Title: {}".format(jsonmangaList.mangaList[index]["Host"],
                                                         jsonmangaList.mangaList[index]["Ignore"],
                                                         jsonmangaList.mangaList[index]["Kitsu ID"],
                                                         jsonmangaList.mangaList[index]["Manga Link"],
                                                         jsonmangaList.mangaList[index]["Manga Type"],
                                                         jsonmangaList.mangaList[index]["Status"],
                                                         jsonmangaList.mangaList[index]["Checked Date"],
                                                         jsonmangaList.mangaList[index]["Title"]))
                                print(
                                    "==========================================="
                                    "============================================")
                            elif user_input == "6":
                                while True:
                                    index_input = input("What index number do you want to jump to?: ")
                                    if index_input.isnumeric():
                                        if int(index_input) < len(noIDs.index):
                                            mangaCounter = int(index_input)
                                            break
                                        else:
                                            print("Index you entered was greater "
                                                  "than the highest manga count: {},"
                                                  "please try again.".format(len(noIDs.index)))
                                    else:
                                        print("Input you entered was not an integer, please try again.")
                                break
                            elif user_input == "7":
                                print("==========================================="
                                      "============================================")
                                jsonmangaList.write_to_json(jsonfile)
                                print("==========================================="
                                      "============================================")
                            elif user_input == "8":
                                print("==========================================="
                                      "============================================")
                                jsonmangaListBackUp.write_to_json(jsonfile)
                                print("==========================================="
                                      "============================================")
                            elif user_input == "9" or user_input == "10":
                                if user_input == "10":
                                    go_back = True
                                else:
                                    # TODO: Add a way to go back to main menu
                                    print("Needs to be added")
                                user_input = input("Would you like to save any unsaved changes? (Y/N): ")
                                if user_input.lower() == "y" or user_input.lower() == "yes":
                                    jsonmangaList.write_to_json(jsonfile)
                                    print("==========================================="
                                          "============================================\n"
                                          "Unsaved changes were saved\n"
                                          "==========================================="
                                          "============================================")
                                else:
                                    print("==========================================="
                                          "============================================\n"
                                          "Unsaved changes were not saved\n"
                                          "==========================================="
                                          "============================================")
                                break
                            else:
                                print("==========================================="
                                      "============================================\n"
                                      "Invalid input\n"
                                      "==========================================="
                                      "============================================")
                    print("You went through the whole list of mangas with no ID.")
                    user_input = input("Would you like to save any unsaved changes? (Y/N): ")
                    if user_input.lower() == "y" or user_input.lower() == "yes":
                        jsonmangaList.write_to_json(jsonfile)
                        print("==========================================="
                              "============================================\n"
                              "Unsaved changes were saved\n"
                              "==========================================="
                              "============================================")

                elif user_input == "4":
                    jsonmangaList.update_df()
                    noIDs = jsonmangaList.mangaDF.loc[jsonmangaList.mangaDF["Kitsu ID"].isna()]
                    print(noIDs[["Title", "Kitsu ID"]])
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

        elif user_input == "8":
            print("Exitting...\n")
            break
        else:
            print("Invalid input\n")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    pd.set_option("display.max_rows", None)
    newList = MangaListExtractor("something-2020-07-11.json")
    oldList = MangaListExtractor("something-old.json")
    newListKitsu = Kitsu("Kitsuneace", "Cookie100203")
    oldListKitsu = Kitsu("Kitsuneace", "Cookie100203")
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

    comparer = MangaComparer(newList, oldList)
    # menu_option()

