import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) 
from data_scraper.CraftNest import CraftNest

class SubCategory:
    def __init__(self):
        self.craftnest  = CraftNest()
        self.page       = None
    
    def setup(self):
        # Get CraftNest ready
        category_links   = self.craftnest.scrape_categories()
        self.page        = self.craftnest.page
        return category_links
    
    def scrape_sub_category(self):
        category_links       = self.setup()
        asset_link_list      = []
        sub_categories_ul    = "body>main>section>div>div>div>div>div:nth-child(2)>div:nth-child(4)>ul"
        sub_category_items   = sub_categories_ul + " > li > a"
        asset_item_selector  = "body >main> section> div> div> div> div> div:nth-child(4)> div >div:nth-child(2)> div > div"
        def scroll_until_no_new_content(page):
            previous_height  = None
            while True:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(2000)  # wait a bit for content to load
                new_height    = page.evaluate("document.body.scrollHeight")
                if new_height == previous_height:
                    break
                previous_height = new_height
        for link in category_links:
            print("Visiting category:", link)
            self.page.goto(link, wait_until="domcontentloaded")
            self.page.wait_for_selector(sub_categories_ul)
            # Get all sub-category links
            sub_elements    = self.page.locator(sub_category_items)
            count           = sub_elements.count()
            print("Total sub-categories found:", count)
            sub_urls = []
            for i in range(count):
                href = sub_elements.nth(i).get_attribute("href")
                name = sub_elements.nth(i).inner_text().strip()
                # Make href absolute if needed
                if href.startswith("/"):
                    href = "https://craftnest.net" + href
                sub_urls.append((name, href))
            # Loop over each sub-category
            for idx, (name, sub_url) in enumerate(sub_urls, start=1):
                print(f"Opening sub-category {idx}/{len(sub_urls)}: {name}")
                print("URL:", sub_url)
                self.page.goto(sub_url, wait_until="domcontentloaded")
                scroll_until_no_new_content(self.page)
                self.page.wait_for_timeout(1200)
                # Get all assets in this sub-category
                assets = self.page.query_selector_all(asset_item_selector)
                print(" Loaded assets:", len(assets))
                for i, asset in enumerate(assets, start=1):
                    a_tag = asset.query_selector("a")
                    if a_tag:
                        asset_link = a_tag.get_attribute("href")
                        print(f"{i}.{asset_link}")
                        asset_link_list.append({
                            "sub_category" : sub_url,
                            "asset"        : asset_link
                        })
            return asset_link_list