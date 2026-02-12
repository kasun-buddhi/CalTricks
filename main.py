from data_scraper.CraftNest import CraftNest
from data_scraper.SubCategory import SubCategory
from data_scraper.Asset import Asset
from data_scraper.DownloadAsset import DownloadAsset
from drive.DriveDataBase import DriveDataBase
import json
import time
import os
from datetime import datetime
from Config import *


class Main:  
    def __init__(self):
        self.craftnest          = CraftNest()
        self.drivedatabase      = DriveDataBase(DOWNLOAD_ASSET_LOCATION)
    
    def download_asset(self):
        """Download assets - one asset per subcategory, upload after each"""
        self.category_links     = self.craftnest.scrape_categories()
        self.subcategory        = SubCategory(self.category_links, self.craftnest.page)
        subcategory_num         = 0
        for sub_urls in self.subcategory.scrape_sub_categories():
            subcategory_num += 1
            print(f"Processing subcategory {subcategory_num}")
            asset       = Asset(sub_urls, self.craftnest.page)
            for item in asset.scrape_asset_links():
                for sub_url, asset_urls in item.items():
                    if asset_urls:
                        last_five   = {sub_url: asset_urls[-5:]}
                        download    = DownloadAsset(last_five, self.craftnest.page)
                        download.download_asset()
                        file_count  = self.get_files_count()
                        print(f"Files downloaded: {file_count}")
                        json_count  = self.get_saved_url_count('links.json')
                        if json_count is not None and json_count > 0:
                            print(f"JSON records: {json_count}")
                            if json_count == file_count:
                                print(f"Verification passed!")
                            else:
                                print(f"Mismatch: JSON={json_count}, Files={file_count}")
                        print(f"Uploading subcategory {subcategory_num} to Google Drive...")
                        self.upload_drive()
                        if os.path.exists('links.json'):
                            os.remove('links.json')
                            print("Cleared links.json for next subcategory")
                        print(f"Subcategory {subcategory_num}")

    def get_files_count(self):
        """Count all files recursively in download directory"""
        total_files = 0
        try:
            for root, dirs, files in os.walk(DOWNLOAD_ASSET_LOCATION):
                total_files += len([f for f in files if os.path.isfile(os.path.join(root, f))])
            return total_files
        except Exception as e:
            print(f"Error counting files: {e}")
            return 0
    
    def get_saved_url_count(self, json_file_path='links.json'):  
        """Get the count of URLs saved in the JSON file"""
        try:
            with open(json_file_path, 'r') as f:
                data = json.load(f)
            return len(data.get('links', []))
        except FileNotFoundError:
            return None
        except json.JSONDecodeError:
            print("Warning: Invalid JSON format")
            return None
    
    def upload_drive(self):
        """Upload and delete the downloaded subcategory"""
        is_upload  = False
        print("\nUploading to Google Drive...")
        # Upload
        self.drivedatabase.upload_asset_folder()
        is_upload == True
        print("Upload complete!")
        if is_upload == True:
            self.drivedatabase.delete_folder(DOWNLOAD_ASSET_LOCATION)   
if __name__ == "__main__":
    m = Main()
    m.download_asset()