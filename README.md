# myfreelapextract
extradata from myfreelap and written into googlesheets

1. download python (should include pip3)
https://www.python.org/

2. download chrome
https://www.google.ca/google_chrome/install

3. download chromedriver (used with selenium)
copy into this folder - rename chromedriver.exe
https://chromedriver.chromium.org/downloads

4. get gooogleAPI credentials file that has access to the googlesheet
# instructions here
https://medium.com/daily-python/python-script-to-edit-google-sheets-daily-python-7-aadce27846c0

5. edit myfreelapcreds.py with your myfreelap credentials

6. install pythone packages
pip3 install selenium
pip install gspread oauth2client

7. run by
python myfreelapextract.py <session title> <tag id(optional)>
