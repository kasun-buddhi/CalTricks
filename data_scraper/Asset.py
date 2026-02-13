import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Config import *


class Asset:
    def __init__(self, sub_category_links,page):
        self.sub_category_links   = sub_category_links
        self.page                 = page  

    def __scroll_until_no_new_content(self, page, selector):
        previous_count      = 0
        no_change_count     = 0
        scroll_times        = 10
        for scroll_num in range(scroll_times):
            page.evaluate("""window.scrollBy({top: window.innerHeight, behavior: 'smooth'});""")
            page.wait_for_timeout(3000)
            new_count   = len(page.query_selector_all(selector))
            print(f"Scroll {scroll_num + 1}: Items loaded: {new_count}")
            if new_count            == previous_count:
                no_change_count     += 1
                if no_change_count  >= 3:
                    print(f"Final count: {new_count}")
                    break
            else:
                no_change_count      = 0
            previous_count           = new_count
        return new_count

    def scrape_asset_links(self):
        asset_item_selector      = "body > main > section > div > div > div > div > div:nth-child(4) > div > div:nth-child(2) > div > div"
        for idx, (name, sub_url) in enumerate(self.sub_category_links, start=1):
            print(f"Opening sub-category {idx}/{len(self.sub_category_links)}: {name}")
            print("URL:", sub_url)
            if self.page is None or self.page.is_closed():
                self.page   = self.page.context.new_page()
            self.page.goto(sub_url, wait_until="domcontentloaded")
            final_count     = self.__scroll_until_no_new_content(self.page, asset_item_selector)
            self.page.wait_for_timeout(1200)
            assets          = self.page.query_selector_all(asset_item_selector)
            print(f"Loaded assets: {len(assets)}")
            # dictionary for this sub-category only
            asset_links     = {sub_url: []}  
            links_found     = 0
            for i, asset in enumerate(assets, start=1):
                a_tag               = asset.query_selector("a")
                if a_tag:
                    asset_link      = a_tag.get_attribute("href")
                    if asset_link:
                        full_url    = "https://craftnest.net" + asset_link
                        asset_links[sub_url].append(full_url)
                        links_found += 1
            print(f"Found {links_found} valid links out of {len(assets)} assets")
            print(f"Completed sub-category: {name}")
            # yield only current sub-category
            yield asset_links  