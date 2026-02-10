import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_scraper.CraftNest import CraftNest
from data_scraper.SubCategory import SubCategory
from data_scraper.Asset import Asset
from drive.DriveDataBase import DriveDataBase
import json
import time
from datetime import datetime
from Config import *


class main:
    def __init__(self):
        self.craftnest         = CraftNest()
        self.drivedatabase     = DriveDataBase(DOWNLOAD_ASSET_LOCATION) 
    
    def download_asset(self):
        self.category_links    = self.craftnest.scrape_categories()
        self.subcategory       = SubCategory(self.category_links,self.craftnest.page)
        for asset_link_dict in self.subcategory.scrape_sub_category():
            print(f"Received asset links: {len(asset_link_dict)} sub-categories processed")
            asset   = Asset(asset_link_dict,self.craftnest.page)
            asset.download_asset()

    def get_files_count(self):
        total_files = 0
        try:
            for root, dirs, files in os.walk(DOWNLOAD_ASSET_LOCATION):
                total_files += len([f for f in files if os.path.isfile(os.path.join(root, f))])
            return total_files
        except Exception as e:
            print(f"Error counting files: {e}")
            return 0
        
    def get_saved_url_count(self):
        json_file_path='link.json'
        try:
            with open(json_file_path, 'r') as f:
                data = json.load(f)
            return len(data)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def wait_for_completion(self, check_interval=30, max_wait_time=28800):
        """
        Wait for downloads to complete by monitoring:
        1. Files appearing in directory (downloads in progress)
        2. link.json creation (all downloads finished)
        3. File count matches URL count (verification)
        """
        start_time      = time.time()
        json_file_path  = 'link.json'
        last_file_count = 0
        while True:
            time_       = time.time() - start_time
            # Check timeout
            if time_ >= max_wait_time:
                print(f"Timeout reached after {time_/3600:.1f} hours")
                return False
            file_count      = self.get_files_count()
            url_count       = self.get_saved_url_count()
            # Show progress
            if file_count != last_file_count:
                print(f"Files downloaded: {file_count}")
                last_file_count = file_count
            else:
                print(f"Waiting... ({file_count} files so far)")
            # Check if link.json exists (signal that downloads are complete)
            if url_count is not None:
                print(f"link.json created!")
                print(f"Total URLs recorded: {url_count}")
                break
            time.sleep(check_interval)
        print("Verifying all files...")
        final_file_count  = self.get_files_count()
        final_url_count   = self.get_saved_url_count(json_file_path)
        print(f"Files in directory: {final_file_count}")
        print(f"URLs in JSON: {final_url_count}")
        if final_file_count == final_url_count and final_url_count > 0:
            return True
        else:
            print(f"Expected: {final_url_count} files")
            print(f"Found: {final_file_count} files")
            print(f"Difference: {abs(final_file_count - final_url_count)} files")
            return True
   
    def upload_drive(self):
        """Wait for downloads to complete, then upload"""
        # Wait for completion (8 hour timeout, 30s check interval)
        for root, dirs, files in os.walk(DOWNLOAD_ASSET_LOCATION):
            print(dirs)
        if self.wait_for_completion(check_interval=30, max_wait_time=300000):
            self.drivedatabase.upload_asset_folder()
            print("Upload complete!")
            self.drivedatabase.delete_local_folder(dirs)
            print("deleted local files")
            return True
        else:
            print("failed!")
            return False


if __name__ == "__main__":
    m  = main()
    m.upload_drive()
    #m.download_asset()

