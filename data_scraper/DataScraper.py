import sys
import os
import gc
import json
import tempfile
import platform
import shutil   
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Config import *


class DataScraper:
    def __init__(self, asset_links,page) :
        self.asset_links   = asset_links 
        self.page          = page
    
    def _extract_folder_name(self,sub_category_url):
        # Extract the relevant part from URL
        # Example: https://craftnest.net/collections/cliparts/afro-american-clipart?sort_by=a-z
        # Returns: cliparts/afro_american_clipart
        # print(sub_category_url)
            if "/collections/" in sub_category_url:
                clean_sub_url    =  sub_category_url.split("?")[0]
                parts            = clean_sub_url.split("/collections/")[-1].split('/')
                if len(parts)   >= 2:
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
        file_path        = os.path.join(download_dir, download.suggested_filename)
        # Check if file already exists
        if os.path.exists(file_path):
            print(f"Already exists, skipping: {download.suggested_filename}")
            return None
        # Save the file
        download.save_as(file_path)
        print(f"Saved the file : {file_path}")
        return file_path
    
    def scrape_data(self):
        title_selector           = "body>main>section>section>div>div>div:nth-child(2)>div:nth-child(3)>h2"
        description_selector     = "body>main>section>section>div>div>div:nth-child(2)>div:nth-child(6)>div>div>p"
        include_selector         = "body>main>section>section>div>div>div:nth-child(2)>div:nth-child(7)>div>div:nth-child(2)>ul"
        tags_selector            = "body>main>section>section>div>div>div:nth-child(2)>div:nth-child(8)>div>div>div>span"
        context                  = self.page.context
        print(f"Getting data {len(self.asset_links)} assets...")
        for i, (asset_url, sub_url) in enumerate(self.asset_links):
            folder_path     = self._extract_folder_name(sub_url)
            download_dir    = os.path.join(DOWNLOAD_ASSET_LOCATION, folder_path)
            


