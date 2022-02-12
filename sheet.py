import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pprint
import logging
import random

# https://medium.com/daily-python/python-script-to-edit-google-sheets-daily-python-7-aadce27846c0
# tutorial is older, so the googple API setup is a little outdated

# call directly to test
# python sheettest.py

# create logger
log = logging.getLogger(__file__)
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(filename)s:%(lineno)d   %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)


#Authorize the API
scope = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file'
    ]
file_name = 'client_key.json'
creds = ServiceAccountCredentials.from_json_keyfile_name(file_name,scope)
client = gspread.authorize(creds)

gsheetfile = 'Dynamic Sprint Velocity Profiling'


# session: this is the text in the 'session' column on myfreelap
#         this script will duplicate sheet and rename it based on session
# tagid: the id for the runner, we'll search for this in the sheet
# splits[]: an array of splits to write into the sheet
def updateEntry(session, tagid, splitsStrings):
    # splits come in like "00:03.06" need to convert to seconds as float
    splits = []
    for s in splitsStrings:
        parts = s.split(':')
        minutes = float(parts[0])
        seconds = float(parts[1])
        splits.append(minutes*60+seconds)

    log.debug(splits)

    # find tagid in roster, if not present, then add one
    sheet = client.open(gsheetfile).worksheet("Athlete Roster")

    # search C6 to C30
    rosterid = sheet.find(tagid)
    rosterIdRow = 0
    rosterIdCol = 3 # 'C'
    if rosterid == None:
        # loop through roster list and find an empty
        rosterlist = sheet.col_value(rosterIdCol) # 'C'
        i = 1
        for r in rosterlist:
            i = i + 1
            if r == "":
                rosterIdRow = i+5 # starts @ C6
                sheet.update_cell(rosterIdRow, rosterIdCol, tagid)
                log.debug("created new tagid at {},{}".format(rosterIdRow, rosterIdCol))
                break
    else:
        rosterIdRow = rosterid.row
        rosterIdCol = rosterid.col
        log.debug("found existing tagid at {},{}".format(rosterIdRow, rosterIdCol))

    # check if the session sheet already exists, if not duplicate it
    try:
        sheet = client.open(gsheetfile).worksheet(session)
    except gspread.SpreadsheetNotFound:
        # duplicate template sheet and rename to session
        log.debug("creating {} from template".format(session))
        client.duplicate_sheet("template", new_sheet_name=session)

    # wait for copied sheet to update with tagid
    # (alternative) determine row of tagid from above)

    # update distance and cones/gates


    # in the session sheet udpate splits
    # splits start in 'G'
    # roster -> session mapping rows
    # 6,7,8,9...   -> 10, 21, 32, 43....
    # https://alteredqualia.com/visualization/hn/sequence/
    splitCol = 7 # 'G'
    for s in splits:
        splitRow = 11*(rosterIdRow-5)-1
        sheet.update_cell(splitRow, splitCol, s)

    # @TODO append trials rather than just overwrite the first one
    #       this way you can see the multiple curves on the plot
    #       there are multiple trials - but we'll just fill in the one for now
    #       since this is just about the dyanmic plotting.


# dump test sheet if this script is ran directly
def main():
    #Fetch the sheet
    sheet = client.open(gsheetfile).worksheet("test")
    # write some crap into column2
    sheet.update('B1', random.randint(1,100))
    sheet.update('B2', random.randint(1,100))
    sheet.update('B3', random.randint(1,100))
    sheet.update('B4', random.randint(1,100))
    sheet.update('B5', random.randint(1,100))
    # dump the sheet
    python_sheet = sheet.get_all_records()
    pp = pprint.PrettyPrinter()
    pp.pprint(python_sheet)

    # test updateEntry()
    session = "Hr6 40yrd WK1"
    tagid = "3 AC-3476"
    splits = ["00:03.06", "00:02.73", "00:03.09"]
    updateEntry(session, tagid, splits)

if __name__ == "__main__":
    main()
