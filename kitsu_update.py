from selenium import webdriver
import pandas as pd
import requests
import time
import json

# Opens our .json file containing the login info for the ktsu website
with open("/home/johnledo/repos/login.json") as json_data:
    logininfo = json.load(json_data)
print(logininfo[0]['Username'])
print(logininfo[0]['Password'])

# Opens our excel file containing the manga list information
mangalist = pd.read_excel("/home/johnledo/repos/Manga Storm/Container/Documents/UserData/MangaList.xlsx")
print(mangalist.loc[5, 'Title'])


# Accesses the necessary driver to use Google Chrome, then this will open the chrome browser
driver = webdriver.Chrome(executable_path='/home/johnledo/repos/Manga-Storm-List/drivers/chromedriver')

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
"""
try:
    response = requests.get('http://kitsu.io/manga/456512')
    if requests < 400:
        print("Webpage exists")
except TypeError:
    print("Webpage does not exist")
"""
# dfs = pd.read_excel('/home/johnledo/repos/Manga Storm/Container/Documents/UserData/MangaList.xlsx', sheetname=None)
# print((pd.DataFrame.from_dict(dfs)))
