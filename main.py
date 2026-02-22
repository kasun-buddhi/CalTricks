import gc
from data_scraper.CraftNest import CraftNest
from data_scraper.SubCategory import SubCategory
from data_scraper.Asset import Asset
from data_scraper.DownloadAsset import DownloadAsset
from drive.DriveDataBase import DriveDataBase
from Config import *


class Main:
    def __init__(self):
        self.craftnest     = CraftNest()
        self.drivedatabase = DriveDataBase(DOWNLOAD_ASSET_LOCATION)
        self.total_assets  = 0
        self.subcategory   = None  
        self.asset         = None  
    
    def restart_browser(self):
        """
        Kill entire Chromium + Node.js process and start fresh.
        Also updates subcategory and asset page references to new browser.
        """
        print(f"[Browser] Restarting after {self.total_assets} assets to free Node.js memory...")
        try:
            self.craftnest.close()
        except Exception as e:
            print(f"[Browser] Error during close: {e}")

        gc.collect()
        self.craftnest     = CraftNest()
        self.craftnest.save_auth()
        self.drivedatabase = DriveDataBase(DOWNLOAD_ASSET_LOCATION)
        #Update page references so old objects use new browser page
        if self.subcategory:
            self.subcategory.page = self.craftnest.page
        if self.asset:
            self.asset.page = self.craftnest.page
        print("[Browser] Browser restarted successfully! Continuing...\n")

    def download_asset(self):
        self.category_links = self.craftnest.scrape_categories()
        self.subcategory    = SubCategory(self.category_links, self.craftnest.page)
        subcategory_num     = 0
        for sub_urls in self.subcategory.scrape_sub_categories():
            subcategory_num += 1
            print(f"[Subcategory] Processing #{subcategory_num}")
            after_four_sub = sub_urls[55:]
            # store as instance variable so restart_browser can update page ref
            self.asset = Asset(after_four_sub, self.craftnest.page)
            asset_num  = 0
            for item in self.asset.scrape_asset_links():
                asset_num         += 1
                self.total_assets += 1
                print(f"\n[Asset] #{asset_num} in subcategory #{subcategory_num} | Total: {self.total_assets}")
                try:
                    download = DownloadAsset([item], self.craftnest.page)
                    download.download_asset()
                    del download
                    gc.collect()
                    self.upload_drive()
                except Exception as e:
                    print(f"[Error] Failed on asset #{asset_num}: {e}")
                    continue
                # Restart browser every N assets to prevent Node.js crash
                if self.total_assets % BROWSER_RESTART_EVERY == 0:
                    self.restart_browser()
            # Cleanup after every subcategory
            print(f"\n[Subcategory #{subcategory_num}] Finished. Cleaning memory...")
            del self.asset
            self.asset = None
            gc.collect()
        print("\n[Main] All subcategories processed successfully!")

    def upload_drive(self):
        """Upload downloaded files to Google Drive and delete local folder"""
        print("[Upload] Uploading to Google Drive...")
        try:
            self.drivedatabase.upload_asset_folder()
            print("[Upload] Upload successful!")
            self.drivedatabase.delete_folder(DOWNLOAD_ASSET_LOCATION)
            print("[Upload] Local folder deleted!")
        except Exception as e:
            print(f"[Upload Error] {e}")

if __name__ == "__main__":
    try:
        m = Main()
        m.download_asset()
    except KeyboardInterrupt:
        print("\n[Stopped] Script stopped by user. Cleaning up...")
    except Exception as e:
        print(f"{e}")
    finally:
        gc.collect()
        print("Exit")