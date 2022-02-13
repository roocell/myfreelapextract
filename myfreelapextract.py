# myfreelapextract.py
# this script will log into myfreelap.com with supplied credentials using selenium
# it will extra data for a given tag and then write it to a googlesheet

# download chromedriver.exe from https://chromedriver.chromium.org/downloads

# usage:
# python myfreelapextract.py <session title> <tag id(optional)>
#  where:
#  <tag id(optional)> supply this argument to use the last run for a tagid
#                     if not given, will search for updated entry and use that.

# python myfreelapextract.py "Hr6 40yrd WK1" "3 AC-3476"
# or to monitor update
#  python myfreelapextract.py "Hr6 40yrd WK1"

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import *
import datetime
import logging
import time
import sys
import sheet
from myfreelapcreds import user
from myfreelapcreds import password

# create logger
log = logging.getLogger(__file__)
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(filename)s:%(lineno)d   %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)

session = sys.argv[1]
if len(sys.argv) > 2:
    tagid = sys.argv[2]
else:
    tagid = ""

url = "https://www.myfreelap.com/"

log.debug("trying {} u:{} p:{}".format(url, user, password))
driver = webdriver.Chrome('./chromedriver.exe')
driver.get(url)
log.debug(driver.title)

loginform = driver.find_element_by_id('new_user_form ')
userfield = driver.find_element_by_name('email')
passwordfield = driver.find_element_by_name('password')
#submitbutton = driver.find_element_by_class_name('btn btn-login submit_btn')
submitbutton = driver.find_element_by_tag_name('button')

userfield.send_keys(user)
passwordfield.send_keys(password)
submitbutton.click()
#driver.execute_script("arguments[0].click();", submitbutton) # perform JS click

# wait for page to load
try:
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "mainpartworkout"))
    )
finally:
    log.debug(driver.title)

# the list of workouts is dynamic data
list = driver.find_elements_by_class_name('view_session_data')
for elm in list:
    log.debug(elm.text)
    if elm.text == session:
        elm.click()
        break

# wait for page to load
try:
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "accordion"))
    )
finally:
    log.debug(driver.title)


# can't cycle through all runs/splits and print because the DOM gets updated
# too frequently and can causes a crash
# get the list of runs
# runs = driver.find_elements_by_id('accordion')
# for run in runs:
#     log.debug(run)
#     # inside according get table
#     # first table is the run data, second table inside the run are the splits
#     try:
#       runtable = run.find_element_by_tag_name("table")
#     except exceptions.StaleElementReferenceException,e:
#         log.debug(e)
#     rows = runtable.find_elements_by_tag_name("td")
#     for row in rows:
#         log.debug(row.text)


# best thing to do is create a while loop and look for the particular tag id
# immediately before the DOM changes
# this could also apply to our 'realtime' behavior we want in the end.

if tagid == "":
    # we're going to look for an updated entry in the loop below
    # but first we need to determine the last one
    #lastEntry = driver.find_element_by_xpath("//div[@id='accordion'][last()]")
    entriesOG =  driver.find_elements_by_id("accordion")
    lastEntry = entriesOG[-1]
    lastTagId = lastEntry.find_elements_by_tag_name("td")[1]
    log.debug("entriesOG {} lastTagId {}".format(len(entriesOG), lastTagId.text))

entry = 0
while True:
    if tagid:
        # find last entry of given tagid
        entries = driver.find_elements_by_xpath('//div[@id="accordion"]//td[contains(text(), "' + tagid + '")]/../../../../../../..')
        entry = entries[-1]
        log.debug("{} {}".format(entry.tag_name, entry.get_attribute('id')))

        # entries =  driver.find_elements_by_id("accordion")
        # for e in entries:
        #     tds = e.find_elements_by_xpath('//td[contains(text(), "' + tagid + '")]')
        #     log.debug("tds cnt {}".format(len(tds)))
        #     if len(tds) > 0:
        #         entry = e
        #         log.debug("found matching entry for {}".format(tagid))
    else:
        # no tagid specified - continue to search for a new entry at the end of the table
        entries =  driver.find_elements_by_id("accordion")
        log.debug("looking for an updated entry {} {}".format(len(entries), len(entriesOG)))
        if len(entries) > len(entriesOG):
            log.debug("detected a new entry")
            entry = entries[-1]
        else:
            time.sleep(1)
            continue

    tds = entry.find_elements_by_tag_name("td")
    instance = tds[0].text
    tagid = tds[1].text
    totalTime = tds[2].text
    # second table is the splits
    tables =  entry.find_elements_by_tag_name("table")
    headerTable = tables[0]
    splitTable = tables[1]

    # click on the headtable to drop it down (otherwise we dont get values)
    driver.execute_script("arguments[0].click();", headerTable) # perform JS click
    time.sleep(0.25) # need to wait a bit for the dropdown to work otherwise no data

    log.debug("{} {} {} {}".format(instance, tagid, totalTime, splitTable.get_attribute("class")))

    # verify that there are splits (laps) here
    numRows = len(splitTable.find_elements_by_tag_name("tr"))
    tds = splitTable.find_elements_by_tag_name("td")
    verifylaps = tds[0]
    log.debug("{} {} {} ".format(numRows, verifylaps.text, tds[1].text))
    if numRows > 0 and "L" not in verifylaps.text:
        log.debug("splits are missing in this entry...ignoring")
        time.sleep(1)
        continue
    lap = []
    laptime = []
    splitTime = []
    # numRows 0,6,12
    for i in range(0,numRows):
        tdsPerRow = 6
        offset = i*tdsPerRow
        lap.append(tds[0+offset].text)
        laptime.append(tds[1+offset].text)
        splitTime.append(tds[2+offset].text)

    log.debug("{} {} {}".format(lap, laptime, splitTime))

    # go and update googlesheets
    log.debug("=======================")
    log.debug("updating googlesheet...")
    log.debug("=======================")
    sheet.updateEntry(session, tagid, splitTime)



    time.sleep(1)
