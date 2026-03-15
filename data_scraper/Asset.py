import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Config import *


class Asset:
    def __init__(self, sub_category_links,page):
        self.sub_category_links   = sub_category_links
        self.page                 = page  


    def __scroll_until_no_new_content(self, page, selector):
        previous_count      = 0
        no_change_count     = 0
        scroll_times        = 4
        for scroll_num in range(scroll_times):
            page.evaluate("""window.scrollBy({top: window.innerHeight, behavior: 'smooth'});""")
            page.wait_for_timeout(3000)
            new_count   = len(page.query_selector_all(selector))
            print(f"Scroll {scroll_num + 1}: Items loaded: {new_count}")
            if new_count            == previous_count:
                no_change_count     += 1
                if no_change_count  >= 2:
                    print(f"Final count: {new_count}")
                    break
            else:
                no_change_count      = 0
            previous_count           = new_count
        return new_count


    def scrape_asset_links(self):
        asset_item_selector = "body > main > section > div > div > div > div > div:nth-child(4) > div > div:nth-child(2) > div > div"
        for idx, (name, sub_url) in enumerate(self.sub_category_links, start=1):
            print(f"Opening sub-category {idx}/{len(self.sub_category_links)}: {name}")
            print("URL:", sub_url)
            # Ensure page is open
            if self.page is None or self.page.is_closed():
                self.page = self.page.context.new_page()
            self.page.goto(sub_url, wait_until="domcontentloaded")
            self.__scroll_until_no_new_content(self.page, asset_item_selector)
            self.page.wait_for_timeout(1200)
            # Extract all hrefs directly from the page, avoiding stale ElementHandles
            hrefs = self.page.eval_on_selector_all(
                f"{asset_item_selector} a",
                "elements => elements.map(a => a.href)")
            print(f"Found links: {len(hrefs)}")
            for href in hrefs:
                if href:
                    # Ensure full URL
                    if not href.startswith("http"):
                        href = "https://craftnest.net" + href
                    yield href, sub_url