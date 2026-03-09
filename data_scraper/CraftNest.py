from playwright.sync_api import sync_playwright
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path
from Config import *


class CraftNest:
    def __init__(self):
        self.url            = "https://craftnest.net"
        self.playwright     = sync_playwright().start()
        self.browser        = self.playwright.chromium.launch(
            headless        = False, 
            args            = [
                            "--disable-gpu",
                            "--disable-dev-shm-usage",               # prevents shared memory crashes
                            "--no-sandbox",                          # reduces memory overhead
                            "--disable-extensions",                  # no extensions = less memory
                            "--disable-background-networking",       # stops background memory usage
                            "--js-flags=--max-old-space-size=512"]) # limit browser JS heap to 512MB
        self.context        = None
        self.page           = None

    def setup_context(self):
        """Creates context — loads saved auth if it exists."""
        if Path(AUTH_FILE).exists():
            self.context = self.browser.new_context(storage_state=AUTH_FILE)
        else:
            self.context = self.browser.new_context()
        self.page = self.context.new_page()

    def is_logged_in(self):
        current_url = self.page.url
        print(f"Current url : {current_url}")
        # Not logged in only if still on login page
        return LOGIN_URL not in current_url

    def login(self):
        username_selector        = "body>main>section>div>div>div>div>div:nth-child(2)>div:nth-child(2)>input"
        username_button_selector = "body>main>section>div>div>div>div>div:nth-child(2)>div:nth-child(3)>button"
        password_selector        = "body>main>section>div>div>div>div>div:nth-child(3)>form>div>input"
        password_button_selector = "body>main>section>div>div>div>div>div:nth-child(3)>form>div:nth-child(6)>button"
        print("[Login] Navigating to login page...")
        self.page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=CRAFTNEST_TIMEOUT)
        # Fill username
        print("[Login] Entering username...")
        self.page.locator(username_selector).wait_for(state="visible", timeout=CRAFTNEST_TIMEOUT)
        self.page.locator(username_selector).fill(USERNAME)
        self.page.locator(username_button_selector).click()
        # Fill password
        print("[Login] Entering password...")
        self.page.locator(password_selector).wait_for(state="visible", timeout=CRAFTNEST_TIMEOUT)
        self.page.locator(password_selector).fill(PASSWORD)
        # Click login and wait for redirect to homepage
        print("[Login] Submitting login form...")
        with self.page.expect_navigation(wait_until="domcontentloaded", timeout=CRAFTNEST_TIMEOUT):
            self.page.locator(password_button_selector).click()
        # Confirm we are no longer on the login page
        current_url = self.page.url
        if LOGIN_URL in current_url:
            raise Exception("[Login] Login failed — still on login page after submit. Check credentials or selectors.")
        print(f"[Login] Login successful! Redirected to: {current_url}")

    def save_auth(self):
        self.setup_context()
        if Path(AUTH_FILE).exists():
            print("[Auth] Found saved auth state, checking if still valid...")
            self.page.goto(self.url, wait_until="domcontentloaded", timeout=CRAFTNEST_TIMEOUT)
            if self.is_logged_in():
                print("[Auth] Session is valid. Already logged in.")
                return
            else:
                print("[Auth] Saved auth state is expired. Re-logging in...")
        self.login()
        Path(AUTH_FILE).parent.mkdir(parents=True, exist_ok=True)
        self.context.storage_state(path=AUTH_FILE)
        print("[Auth] Auth state saved!")
        print("[Auth] Site url is:", self.url)

    def scrape_categories(self):
        self.save_auth()
        category_links = []
        self.page.wait_for_selector("ul.tmenu_nav")
        categories = self.page.locator("ul.tmenu_nav > li.tmenu_item")
        count      = categories.count()
        for index in range(count):
            item        = categories.nth(index)
            link        = item.locator("a.tmenu_item_link")
            href        = link.get_attribute("href")
            if href.startswith("/"):
                href    = "https://craftnest.net" + href
            sorted_href = href + "?sort_by=a-z"
            category_links.append(sorted_href)
        return category_links

    def close(self):
        """Cleanly close page, context, browser, and playwright to free Node.js memory."""
        print("[Browser] Closing browser...")
        try:
            if self.page and not self.page.is_closed():
                self.page.close()
        except Exception as e:
            print(f"[Browser] Page close error: {e}")
        try:
            if self.context:
                self.context.close()
        except Exception as e:
            print(f"[Browser] Context close error: {e}")
        try:
            if self.browser:
                self.browser.close()
        except Exception as e:
            print(f"[Browser] Browser close error: {e}")
        try:
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            print(f"[Browser] Playwright stop error: {e}")
        self.page       = None
        self.context    = None
        self.browser    = None
        self.playwright = None
        print("[Browser] Browser fully closed and memory freed!")