from playwright.sync_api import sync_playwright
import os
from pathlib import Path
from Config import *


class CraftNest:
    def __init__(self,url):
        self.url            = url
        self.playwright     = sync_playwright().start()
        self.browser        = self.playwright.chromium.launch(headless=False, args=["--disable-gpu"])
        self.context        = None
        self.page           = None

    def setup_context(self):
        """Creates context — loads saved auth if it exists."""
        if Path(AUTH_FILE).exists():
            self.context    = self.browser.new_context(storage_state=AUTH_FILE)
        else:
            self.context    = self.browser.new_context()
        self.page           = self.context.new_page()
    
    def is_logged_in(self):
        current_url = self.page.url
        print(f"Current url : {current_url}")
        return LOGIN_URL not in current_url

    def login(self):
        username_selector                     = "body>main>section>div>div>div>div>div:nth-child(2)>div:nth-child(2)>input"
        username_button_selector              = "body>main>section>div>div>div>div>div:nth-child(2)>div:nth-child(3)>button"
        password_selector                     = "body>main>section>div>div>div>div>div:nth-child(3)>form>div>input"
        password_button_selector              = "body>main>section>div>div>div>div>div:nth-child(3)>form>div:nth-child(6)>button"
        self.page.goto(LOGIN_URL, wait_until  = "domcontentloaded",timeout = CRAFTNEST_TIMEOUT)
        # username
        self.page.locator(username_selector).wait_for(state = "visible",timeout= CRAFTNEST_TIMEOUT)
        self.page.locator(username_selector).fill(USERNAME)
        self.page.locator(username_button_selector).click()
        # password
        self.page.locator(password_selector).wait_for(state = "visible",timeout = CRAFTNEST_TIMEOUT)
        self.page.locator(password_selector).fill(PASSWORD)
        self.page.locator(password_button_selector).click()
        # wait for redirect after login
        self.page.wait_for_timeout(CRAFTNEST_TIMEOUT)
        self.page.goto(self.url, wait_until  = "domcontentloaded", timeout = CRAFTNEST_TIMEOUT)
        print("Login successful!")
    
    def save_auth(self):
        self.setup_context()
        if Path(AUTH_FILE).exists():
            self.page.goto(self.url, wait_until="domcontentloaded", timeout = CRAFTNEST_TIMEOUT)
            if self.is_logged_in():
                print("Session is valid. Already logged in.")
                return                          
            else:
                print("Saved auth state is expired. Re-logging in...")
        self.login()
        Path(AUTH_FILE).parent.mkdir(parents = True, exist_ok = True)
        self.context.storage_state(path      = AUTH_FILE)
        print("Auth state saved!")
        print("Site url is :",self.url)