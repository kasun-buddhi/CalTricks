from playwright.sync_api import sync_playwright
from pathlib import Path
from Config import *


class CraftNest:
    def __init__(self):
        self.url            = "https://craftnest.net"
        self.playwright     = sync_playwright().start()
        self.browser        = self.playwright.chromium.launch(
        headless            = True,
        args                = [
                            "--disable-gpu",
                            "--disable-dev-shm-usage",
                            "--no-sandbox",
                            "--disable-extensions",
                            "--disable-background-networking",
                            "--disable-background-timer-throttling",
                             "--disable-renderer-backgrounding",
                            "--js-flags=--max-old-space-size=512"])
        self.context        = None
        self.page           = None


    def setup_context(self):
        """Creates context — loads saved auth if it exists."""
        if Path(AUTH_FILE).exists():
            self.context    = self.browser.new_context(storage_state = AUTH_FILE)
        else:
            self.context    = self.browser.new_context()
        self.page           = self.context.new_page()
        self.page.set_default_timeout(60000)


    def is_logged_in(self):
        current_url     = self.page.url
        print(f"Current url : {current_url}")
        return LOGIN_URL not in current_url


    def login(self):
        print("Navigating to login page...")
        self.page.goto(LOGIN_URL, wait_until   = "domcontentloaded", timeout = CRAFTNEST_TIMEOUT)
        #fill email
        self.page.locator("#CustomerEmailStep1").wait_for(state = "visible", timeout = CRAFTNEST_TIMEOUT)
        self.page.locator("#CustomerEmailStep1").fill(USERNAME)
        # click Login button
        self.page.locator("button[type  ='button']:has-text('Login')").click()
        self.page.wait_for_timeout(2000)
        # fill password
        self.page.locator("#CustomerPassword").wait_for(state = "visible", timeout  = CRAFTNEST_TIMEOUT)
        self.page.locator("#CustomerPassword").fill(PASSWORD)
        # submit
        self.page.locator("button[type  ='submit']").click()
        self.page.wait_for_load_state("domcontentloaded", timeout = CRAFTNEST_TIMEOUT)
        self.page.wait_for_timeout(3000)
        self.page.goto(self.url, wait_until = "domcontentloaded", timeout = CRAFTNEST_TIMEOUT)
        print("Login successful!")


    def save_auth(self):
        self.setup_context()
        if Path(AUTH_FILE).exists():
            self.page.goto(self.url, wait_until = "domcontentloaded", timeout = CRAFTNEST_TIMEOUT)
            if self.is_logged_in():
                print("Session is valid. Already logged in.")
                return
            else:
                print("Saved auth state is expired. Re-logging in...")
        self.login()
        Path(AUTH_FILE).parent.mkdir(parents = True, exist_ok = True)
        self.context.storage_state(path = AUTH_FILE)
        print("Auth state saved!")
        print("Site url is :", self.url)

    
    def scrape_categories(self):
        self.save_auth()
        category_links  = []
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_selector("ul.tmenu_nav", state="visible", timeout=60000)
        categories  = self.page.locator("ul.tmenu_nav > li.tmenu_item")
        count       = categories.count()
        print(f"Found {count} categories.")
        for index in range(count):
            item    = categories.nth(index)
            link    = item.locator("a.tmenu_item_link")
            href    = link.get_attribute("href")
            if not href:
                print(f"[Warning] Category {index} has no href, skipping.")
                continue
            if href.startswith("/"):
                href        = "https://craftnest.net" + href
            sorted_href     = href + "?sort_by=a-z"
            category_links.append(sorted_href)
        return category_links

    
    def close(self):
        """Cleanly close page, context, browser, and playwright to free memory."""
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
        self.page           = None
        self.context        = None
        self.browser        = None
        self.playwright     = None
        print("[Browser] Browser fully closed.")