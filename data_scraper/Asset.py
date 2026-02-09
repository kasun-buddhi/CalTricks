import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Config import *


class Asset:
    def __init__(self, sub_category_links,page) :
        self.sub_category_links     = sub_category_links
        self.page                   = page
    
    def _extract_folder_name(self,sub_category_url):
        # Extract the relevant part from URL
        # Example: https://craftnest.net/collections/cliparts/afro-american-clipart?sort_by=a-z
            # Returns: cliparts/afro_american_clipart
            #print(sub_category_url)
            if "/collections/" in sub_category_url:
                clean_sub_url   =  sub_category_url.split("?")[0]
                parts           = clean_sub_url.split("/collections/")[-1].split('/')
                if len(parts)  >= 2:
                # Return last two parts: category/sub-category
                    folder_name    = f"{parts[0]}/{parts[1]}"
                elif len(parts)    == 1:
                    # Only category
                    folder_name    = parts[0]
                else:
                    return "unknown"
                #print(folder_name)
                return folder_name.replace('-','_')
            return "unknown"   
        
    def _save_file_local(self, download, download_dir):
        """
        Save downloaded file to local directory
            download        : Playwright download object
            download_dir    : Target directory path
            Returns         : File path if saved, None if skipped
        """
        file_path       = os.path.join(download_dir, download.suggested_filename)
        # Check if file already exists
        if os.path.exists(file_path):
            print(f"Already exists, skipping: {download.suggested_filename}")
            return None
        # Save the file
        download.save_as(file_path)
        print(f"Saved the file : {file_path}")
        return file_path
    
    def download_asset(self):
        download_button_selector      =  "body>main>section>section>div>div>div:nth-child(2)>div:nth-child(4)>a"
        new_download_selector         =  "body>astro-island>div>div>div:nth-child(1)>div:nth-child(2)>div>div>nav>ol>li>button>span"
        zip_download_selector         =  "body>div>div"
        print(f"Received {len(self.sub_category_links)} sub-categories to download")
        for sub_category_url, asset_list in self.sub_category_links.items():
            # Extract category/sub-category path from URL
            folder_path      = self._extract_folder_name(sub_category_url)
            # Create full directory path: Asset/cliparts/afro_american_clipart/
            download_dir     = os.path.join(DOWNLOAD_ASSET_LOCATION, folder_path)
            os.makedirs(download_dir, exist_ok = True)
            print(f"Sub-category: {sub_category_url}")
            print(f"Download location: {download_dir}")
            print(f"Total assets: {len(asset_list)}")
            for idx, asset_url in enumerate(asset_list, start = 1):
                print(f"[{idx}/{len(asset_list)}] Downloading asset: {asset_url}")
                try:
                    self.page.goto(asset_url, wait_until = "domcontentloaded", timeout  = 180000)
                    self.page.locator(download_button_selector).click()
                    old_page          = self.page
                    with self.page.context.expect_page() as new_page_info:
                        new_page      = new_page_info.value
                        self.page     = new_page
                        self.page.set_default_timeout(120000)
                    old_page.close()
                    self.page.wait_for_selector(new_download_selector, timeout = 180000)
                    self.page.locator(new_download_selector).click()
                    with self.page.expect_download(timeout = 300000) as download_info:
                        self.page.locator(zip_download_selector).click()
                    download      = download_info.value
                    if self._save_file_local(download, download_dir) is None:
                        # File already exists, skip to next
                        continue  
                except Exception as e:
                    print(f"Error downloading {asset_url}: {e}")
                    continue   
                print(f"Completed download sub category : {sub_category_url}")