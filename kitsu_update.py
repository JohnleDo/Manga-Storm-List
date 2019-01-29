from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from multiprocessing import Manager, Pool, cpu_count, Queue
import pandas as pd
import time
import json
from tqdm import tqdm

"""
------------------
TO DO
------------------
1. Organize the code better by adding functions.
2. Implement multiprocessing/multithreading for selenium so it can update the kitsu website quicker.
3. Figure out how to check if a website exist because for some reason using the existing methods to check if a kitsu website exist returns a 403 error
whether they exist or not. An idea is to simply do the method to creating website links, store it into a list or something; run the website updater. When
the website it loaded it will check for a header element with the text 404. If it doesn't exist then website exist and the website will be added to the
.xlsx file.
"""
mangalist = pd.read_excel("/home/johnledo/repos/Manga Storm/Container/Documents/UserData/MangaList.xlsx")
manager = Manager()
# shared_list = manager.list()
# shared_queue = manager.Queue()


def login(xy):
    driver = webdriver.Chrome(executable_path='/home/johnledo/repos/Manga-Storm-List/drivers/chromedriver')

    # Opens our .json file containing the login info for the ktsu website
    with open("/home/johnledo/repos/login.json") as json_data:
        logininfo = json.load(json_data)

    # This will access a webpage after opening the browser from eariler
    driver.get('http://kitsu.io/')

    # Clicks the signin button but before we do that we delay our program for a few seconds or it will search the webpage for the xpath before it shows up
    # Time delay varies on the speed the page or item loads up
    time.sleep(1)
    xpath = '//*[@id="sign-in-button"]'
    signin_btn = driver.find_element_by_xpath(xpath)
    signin_btn.click()

    # Finds the email text area and fill its in
    # Time delay varies on the speed the page or item loads up
    time.sleep(2)
    xpath = '//*[@id="ember336"]/div/div[2]/form/div[1]/input[1]'
    signin_username = driver.find_element_by_xpath(xpath)
    signin_username.send_keys(logininfo[0]['Username'])

    # Finds the password text area and fill its in
    # Time delay varies on the speed the page or item loads up
    xpath = '//*[@id="ember336"]/div/div[2]/form/div[1]/input[2]'
    signin_password = driver.find_element_by_xpath(xpath)
    signin_password.send_keys(logininfo[0]['Password'])

    # Clicks the login button after filling out the credientials to login
    xpath = '//*[@id="ember336"]/div/div[2]/form/div[2]/button'
    login_btn = driver.find_element_by_xpath(xpath)
    login_btn.click()


if __name__ == "__main__":
    """
    for x in range(800):
        shared_queue.put(int(x))

    print(shared_queue.get())
    """
    cores = cpu_count()
    print("Number of Cores:", cores)
    iteration = list(range(0, cores))
    pool = Pool()
    """
    for x in tqdm(pool.imap(login, iteration), total=len(iteration)):
        pass
    pool.close()
    pool.join()
    """

    """
    for x in range(0, 6):
        print(mangalist.loc[x]['ENG Title'])
    try:
        response = requests.get('https://kitsu.io/manga/boku-no-hero-academia')
        if response < 400:
            print("Webpage exists")
    except TypeError:
        print("Webpage does not exist")
"""
"""
    for x in range(len(mangalist)):
        temp = mangalist.loc[x]
        if temp['Kitsu Link'] is not None:
            mangasite = temp['ENG Title'].replace(',', '')
            mangasite = mangasite.replace(' - ', '-')
            mangasite = mangasite.replace(' ', '-').lower()
            mangasite = 'http://kitsu.io/manga/' + mangasite
            try:
                response = requests.get(mangasite)
                if response.status_code < 400:
                    temp['Kitsu Link'] = mangasite
                    mangalist.loc[x] = temp
                    print("Webpage exists: ", mangasite)
            except TypeError:
                print("Webpage does not exist: ", mangasite)
"""
"""
    # Accesses the necessary driver to use Google Chrome, then this will open the chrome browser
    driver = webdriver.Chrome(executable_path='/home/johnledo/repos/Manga-Storm-List/drivers/chromedriver')

    login(driver)

    time.sleep(1)
    driver.get('https://kitsu.io/manga/boku-no-hero-academia')

    time.sleep(3)
    try:
        editButton = driver.find_element_by_xpath("//button[text()='Started Reading']")
        # editButton.click()
    except NoSuchElementException:
        editButton = driver.find_element_by_xpath("//button[text()='Edit Library Entry']")
    # editButton = driver.find_element_by_xpath("//button[text()='Edit Library Entry']")
    editButton.click()
    """

# dfs = pd.read_excel('/home/johnledo/repos/Manga Storm/Container/Documents/UserData/MangaList.xlsx', sheetname=None)
# print((pd.DataFrame.from_dict(dfs)))
