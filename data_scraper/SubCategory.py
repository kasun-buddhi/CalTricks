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
        category_links = self.craftnest.scrape_categories()
        self.page = self.craftnest.page
        return category_links

    def scrape_sub_category(self):
        category_links         = self.setup()
        sub_categories_url     = []
        #print(category_links)
        sub_categories_ul      = "body>main>section>div>div>div>div>div:nth-child(2)>div:nth-child(4)>ul"
        sub_category_items     = sub_categories_ul + " > li > a"
        asset_item_selector    = "body>main>section>div>div>div>div>div:nth-child(4)>div>div:nth-child(2)>div>div"
        def scroll_page(page):
            previous_height    = None
            while True:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                # wait a bit for content to load
                page.wait_for_timeout(2000) 
                new_height    = page.evaluate("document.body.scrollHeight")
                if new_height == previous_height:
                    break
                previous_height = new_height
        for link in category_links:
            print("category:", link)
            self.page.goto(link, wait_until = "domcontentloaded")
            self.page.wait_for_selector(sub_categories_ul)
            sub_elements         = self.page.locator(sub_category_items)
            sub_category_count   = sub_elements.count()
            print("Total sub-categories found:", sub_category_count)
            for i in range(sub_category_count):
                href = sub_elements.nth(i).get_attribute("href")
                #name = sub_elements.nth(i).inner_text().strip()
                sub_categories_url.append(href)
            
            

            
        
        
        
        
        
        
        
        
        
        """
        category_links       = self.setup()
        sub_categories_ul    = "body>main>section>div>div>div>div>div:nth-child(2)>div:nth-child(4)>ul"
        sub_category_items   = sub_categories_ul + " > li > a"
        asset_item_selector  = "body main section div div div div div:nth-child(4) div div:nth-child(2) div > div"
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
            print("\nVisiting category:", link)
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
                print(f"\n → Opening sub-category {idx}/{len(sub_urls)}: {name}")
                print("URL:", sub_url)

                self.page.goto(sub_url, wait_until="domcontentloaded")
                scroll_until_no_new_content(self.page)
                self.page.wait_for_timeout(1200)

                # Get all assets in this sub-category
                assets = self.page.query_selector_all(asset_item_selector)
                print("   Loaded assets:", len(assets))

                for i, asset in enumerate(assets, start=1):
                    a_tag = asset.query_selector("a")
                    if a_tag:
                        asset_link = a_tag.get_attribute("href")
                        print(f"      {i}. {asset_link}")

            """

    """
    def scrape_sub_category(self):
        category_links       = self.setup()
        sub_categories_ul    = "body>main>section>div>div>div>div>div:nth-child(2)>div:nth-child(4)>ul"
        sub_category_items   = sub_categories_ul + " > li > a"
        asset_item_selector  = "body main section div div div div div:nth-child(4) div div:nth-child(2) div > div"
        for link in category_links:
            print("category:", link)
            self.page.goto(link, wait_until="domcontentloaded")

            # wait for sub category list
            self.page.wait_for_selector(sub_categories_ul)
            x = self.page.locator(sub_category_items).inner_text

            # get ALL <li><a> items
            items = self.page.query_selector_all(sub_category_items)
            


            print("Total sub-categories found:", len(items),x)
            def scroll_until_no_new_content(page):
                previous_height = None
                while True:
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(3000)
                    new_height = page.evaluate("document.body.scrollHeight")
                    if new_height == previous_height:
                        break
                    previous_height = new_height
            scroll_until_no_new_content(self.page)
            assets = self.page.query_selector_all(asset_item_selector)
            print("Loaded assets:", len(assets))
            for idx, asset in enumerate(assets, start=1):
                a_tag = asset.query_selector("a")
                if a_tag:
                    asset_link = a_tag.get_attribute("href")
                    print(f"{idx}. {asset_link}")

        
        
            for idx, item in enumerate(items, start=1):
                href = item.get_attribute("href")
                text = item.inner_text().strip()
                print(f"{idx}. {text} — {href}")
        
    """
    
    
    
    """
    def scrape_sub_category(self):
        category_links          = self.setup()
       
    
        
        
        # ❗ You must update this selector later to target EACH asset item
        asset_item_selector     = "body main section div div div div div:nth-child(4) div div:nth-child(2) div > div"
        
        # ----- Infinite Scroll Function -----
        def scroll_until_no_new_content(page):
            previous_height = None
            while True:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(20000)
                new_height = page.evaluate("document.body.scrollHeight")
                if new_height == previous_height:
                    break
                previous_height = new_height

        # ----- Main Loop -----
        for link in category_links:
            print("\nVisiting category:", link)
            self.page.goto(link, wait_until="domcontentloaded")

            # Load everything on the page
            scroll_until_no_new_content(self.page)

            # Get all assets
            assets = self.page.query_selector_all(asset_item_selector)
            print("Loaded assets:", len(assets))

            # Extract asset links
            for idx, asset in enumerate(assets, start=1):
                a_tag = asset.query_selector("a")
                if a_tag:
                    asset_link = a_tag.get_attribute("href")
                    print(f"{idx}. {asset_link}")
    
          """
 