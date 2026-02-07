import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) 
from   data_scraper.SubCategory import SubCategory
from Config import *


class Asset:
    def __init__(self, craftnest):
        self.craftnest      = craftnest
        self.subcategory    = SubCategory(self.craftnest)
        self.browser        = self.craftnest.browser
    
    def extract_folder_name(self, url):
        """Extract clean folder name from URL"""
        # Extract the relevant part from URL
        # Example: https://craftnest.net/collections/cliparts/afro-american-clipart?sort_by=a-z
        # Returns: afro-american-clipart
        if '/collections/' in url:
            # Remove query parameters
            clean_url   = url.split('?')[0]
            # Get the part after /collections/
            parts       = clean_url.split('/collections/')[-1].split('/')
            if len(parts) >= 2:
                # Return last two parts: category/sub-category
                return f"{parts[0]}/{parts[1]}"
            elif len(parts) == 1:
                # Only category
                return parts[0]
        return "unknown"
    
    def download_asset(self):
        download_button_selector = "body>main>section>section>div>div>div:nth-child(2)>div:nth-child(4)>a"
        new_download_selector    = "body>astro-island>div>div>div:nth-child(1)>div:nth-child(2)>div>div>nav>ol>li>button>span"
        zip_download_selector    = "body>div>div"
        # Ensure base folder exists
        os.makedirs(DOWNLOAD_ASSET_LOCATION, exist_ok=True)
        # Iterate over the generator
        for asset_links in self.subcategory.scrape_sub_category():
            print(f"Received {len(asset_links)} sub-categories to download")
            for sub_category_url, asset_list in asset_links.items():
                # Extract category/sub-category path from URL
                folder_path     = self.extract_folder_name(sub_category_url)
                # Create full directory path: Asset/cliparts/afro-american-clipart/
                download_dir    = os.path.join(DOWNLOAD_ASSET_LOCATION, folder_path)
                os.makedirs(download_dir, exist_ok=True)
                print(f"Sub-category: {sub_category_url}")
                print(f"Download location: {download_dir}")
                print(f"Total assets: {len(asset_list)}")
                for idx, asset_url in enumerate(asset_list, start=1):
                    print(f"[{idx}/{len(asset_list)}] Downloading asset: {asset_url}")
                    try:
                        self.craftnest.page.goto(asset_url, wait_until="domcontentloaded", timeout=180000)
                        self.craftnest.page.locator(download_button_selector).click()
                        with self.craftnest.page.context.expect_page() as new_page_info:
                            new_page = new_page_info.value
                            self.craftnest.page = new_page
                            self.craftnest.page.set_default_timeout(120000)
                        self.craftnest.page.wait_for_selector(new_download_selector, timeout=180000)
                        self.craftnest.page.locator(new_download_selector).click()
                        with self.craftnest.page.expect_download(timeout=300000) as download_info:
                            self.craftnest.page.locator(zip_download_selector).click()
                        download = download_info.value
                        # Save to organized folder structure
                        file_path = os.path.join(download_dir, download.suggested_filename)
                        # Check if file already exists
                        if os.path.exists(file_path):
                            print(f"Already exists, skipping: {download.suggested_filename}")
                            continue
                        download.save_as(file_path)
                        print(f"Downloaded: {file_path}")
                    except Exception as e:
                        print(f"Error downloading {asset_url}: {e}")
                        continue
                print(f"Completed sub-category: {sub_category_url}")
        print("All downloads completed!")
        self.browser.close()