import os

AUTH_FILE                       = "playwright/.auth/state.json"
USERNAME                        = ""
PASSWORD                        = ""
LOGIN_URL                       = "https://craftnest.net/account/login"
CRAFTNEST_TIMEOUT               = 100000
DOWNLOAD_ASSET_LOCATION         = "./Asset"                                   # local root — folders go here as: ./Asset/cliparts/afro_american_clipart/
TOKEN_PATH                      = "/root/testing_/token.json"                 # generated after first auth
CREDENTIALS_PATH                = "/root/credentials.json"                    # Google Cloud client secrets
DRIVE_SCOPES                    = ['https://www.googleapis.com/auth/drive']   # full scope needed to read/rename existing folders
GOOGLE_DRIVE_PARENT_FOLDER_ID   = "19NBQp4n6zUMjAfjzcjNAB9n9tSg14-Ad" 
BROWSER_RESTART_EVERY           = 10
