from data_scraper.CraftNest import CraftNest
from data_scraper.SubCategory import SubCategory
from data_scraper.Asset import Asset
from drive.DriveDataBase import DriveDataBase
from Config import *

class main:
    def __init__(self):
        self.craftnest         = CraftNest()
        self.page              = self.craftnest.page
        #self.subcategory       = SubCategory(self.category_links,self.page)
        self.drivedatabase     = DriveDataBase(DOWNLOAD_ASSET_LOCATION) 
    
    def download_asset(self):
        self.category_links    = self.craftnest.scrape_categories()
        self.subcategory       = SubCategory(self.category_links,self.page)
        for asset_link_dict in self.subcategory.scrape_sub_category():
            print(f"Received asset links: {len(asset_link_dict)} sub-categories processed")
            asset   = Asset(asset_link_dict,self.page)
            asset.download_asset()

    def upload_drive(self):
        file_path   = self.drivedatabase.upload_asset_folder()
        print(file_path)


m = main()
m.upload_drive()

