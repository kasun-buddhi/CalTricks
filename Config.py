import os

AUTH_FILE                           = "playwright/.auth/state.json"
USERNAME                            =  os.getenv("CRAFTNEST_USERNAME")
PASSWORD                            =  os.getenv("CRAFTNEST_PASSWORD")
LOGIN_URL                           = "https://craftnest.net/account/login"
CRAFTNEST_TIMEOUT                   = 100000
DOWNLOAD_ASSET_LOCATION             = "./Asset"
TOKEN_PATH                          = os.getenv("TOKEN_PATH")
DRIVE_SCOPES                        = ['https://www.googleapis.com/auth/drive.file']
GOOGLE_DRIVE_PARENT_FOLDER_ID       = "117xKnajtunTH0XX_s9dwClUy_KaptS5Q"
BROWSER_RESTART_EVERY               = 10