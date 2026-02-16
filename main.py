from data_scraper.CraftNest import CraftNest
from data_scraper.SubCategory import SubCategory
from data_scraper.Asset import Asset
from data_scraper.DownloadAsset import DownloadAsset
from drive.DriveDataBase import DriveDataBase
from Config import *


class Main:  
    def __init__(self):
        self.craftnest          = CraftNest()
        self.drivedatabase      = DriveDataBase(DOWNLOAD_ASSET_LOCATION)
    
    def download_asset(self):
        self.category_links = self.craftnest.scrape_categories()
        self.subcategory = SubCategory(self.category_links, self.craftnest.page)
        subcategory_num = 0
        for sub_urls in self.subcategory.scrape_sub_categories():
            subcategory_num += 1
            print(f"Processing subcategory {subcategory_num}")
            asset = Asset(sub_urls, self.craftnest.page)
            for item in asset.scrape_asset_links():
                # Download the asset
                download = DownloadAsset([item], self.craftnest.page)
                download.download_asset()  
                # Upload immediately after download
                self.upload_drive()

    def upload_drive(self):
        """Upload and delete the downloaded subcategory"""
        is_upload = False
        print("Uploading to Google Drive...")
        # Upload
        self.drivedatabase.upload_asset_folder()
        is_upload = True  
        if is_upload:
            try:
                self.drivedatabase.delete_folder(DOWNLOAD_ASSET_LOCATION)
                print("folder deleted!")
            except Exception as e:
                print(f"delete Error : {e}")

if __name__ == "__main__":
    try:
        m = Main()
        m.download_asset()
    except KeyboardInterrupt:
        print("\nStopped by user. Cleaning up safely...")
