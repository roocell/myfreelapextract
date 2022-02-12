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

alphabet = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L",
            "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "X", "Y", "Z"]

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

    # find tagid in roster, if not present, then add one
    sheet = client.open(gsheetfile).worksheet("Athlete Roster")

    # search C6 to C30
    rosterid = sheet.find(tagid)
    rosterIdRow = 0
    rosterIdCol = 3 # 'C'
    if rosterid == None:
        # loop through roster list and find an empty
        rosterlist = sheet.col_values(rosterIdCol) # 'C'
        i = 0
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
    except gspread.exceptions.WorksheetNotFound:
        # duplicate template sheet and rename to session
        sheet = client.open(gsheetfile).worksheet("template")
        log.debug("creating {} from template".format(session))
        sheet.duplicate(insert_sheet_index=None, new_sheet_name=session)
        sheet = client.open(gsheetfile).worksheet(session)

        # update distance and cones/gates
        cones = len(splits)+1
        distance = 40
        if "60" in session:
            distance = 60
        elif "100" in session:
            distance = 100
        log.debug("updating distance and cones {} {}".format(distance, cones))
        sheet.update_cell(3, 8, distance) # H3
        sheet.update_cell(3, 12, cones) # L3

        # need to delete the "Cone / Gate Placement" rows that aren't required.
        # J6:P6
        #cell = sheet.find("Cone / Gate Placement")
        log.debug("clearing Cone / Gate Placement to fix plot x-axis")
        start = alphabet[alphabet.index("G") + len(splits)] + str(6)
        end = "P6"
        cell_list = sheet.range(start + ":" + end)
        for i, val in enumerate(cell_list):
            cell_list[i].value = ""
        sheet.update_cells(cell_list)


    # wait for copied sheet to update with tagid
    # (alternative) determine row of tagid from above)

    # in the session sheet udpate splits
    # splits start in 'G'
    # roster -> session mapping rows
    # 6,7,8,9...   -> 10, 21, 32, 43....
    # https://alteredqualia.com/visualization/hn/sequence/

    splitCol = 7 # 'G'
    for i, s in enumerate(splits):
        splitRow = 11*(rosterIdRow-5)-1
        sheet.update_cell(splitRow, splitCol+i, s)
    log.debug(splits)

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
