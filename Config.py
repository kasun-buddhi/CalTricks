import os

AUTH_FILE           = "playwright/.auth/state.json"
USERNAME            =  os.getenv("CRAFTNEST_USERNAME")
PASSWORD            =  os.getenv("CRAFTNEST_PASSWORD")
LOGIN_URL           = "https://craftnest.net/account/login"
CRAFTNEST_TIMEOUT   = 10000
