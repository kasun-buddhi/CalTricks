import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) 
from   data_scraper.SubCategory import SubCategory
from Config import *

class Asset:
    def __init__(self,craftnest):
        self.craftnest      = craftnest
        self.subcategory    = SubCategory(self.craftnest)
        self.page           = None
    
    def setup(self):
        asset_links         = self.subcategory.scrape_sub_category()
        self.page           = self.craftnest.page
        return asset_links
    
    def download_asset(self):
        asset_links                 = self.setup()
        download_button_selector    = "body>main>section>section>div>div>div:nth-child(2)>div:nth-child(4)>a"
        new_download_selector       = "body>astro-island>div>div>div:nth-child(1)>div:nth-child(2)>div>div>nav>ol>li>button>span"
        zip_downlaod_selector       = "body>div>div"
        for sub_category, asset_list in asset_links.items():
            for asset_url in asset_list:
                print(f"asset_url : {asset_url}")
                self.page.goto(asset_url, wait_until="domcontentloaded")
                self.page.locator(download_button_selector).click()
                self.page.wait_for_selector(download_button_selector)
                with self.page.context.expect_page() as new_page_info:
                    new_page   = new_page_info.value
                    self.page  = new_page
                self.page.wait_for_selector(new_download_selector,timeout=3000)
                self.page.locator(new_download_selector).click()
                with self.page.expect_download() as download_info:
                     self.page.locator(zip_downlaod_selector).click()
                download  = download_info.value
                file_path = download.save_as(DOWNLOAD_ASSET_LOCATION)
                print("Downloaded file location:",file_path) 
                print("Download completed!")                     