import gc
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
        self.total_assets       = 0
    
    def restart_browser(self):
        """
        Kill the entire Chromium + Node.js process and start fresh.
        This is the REAL fix for the JavaScript heap out of memory error.
        """
        print(f"[Browser] Restarting after {self.total_assets} assets to free memory...")
        try:
            # close page + context + browser + playwright
            self.craftnest.close()     
        except Exception as e:
            print(f"[Browser] Error during close: {e}")
        # free Python memory too
        gc.collect()                   
        # Start a completely fresh browser
        self.craftnest     = CraftNest()
        # re-login with saved session
        self.craftnest.save_auth()      
        self.drivedatabase = DriveDataBase(DOWNLOAD_ASSET_LOCATION)
        print("[Browser] Browser restarted successfully! Continuing...\n")
    
    def download_asset(self):
        self.category_links     = self.craftnest.scrape_categories()
        self.subcategory        = SubCategory(self.category_links, self.craftnest.page)
        subcategory_num         = 0
        for sub_urls in self.subcategory.scrape_sub_categories():
            subcategory_num     += 1
            print(f"[Subcategory] Processing #{subcategory_num}")
            after_four_sub      = sub_urls[40:]
            asset               = Asset(after_four_sub, self.craftnest.page)
            asset_num           = 0
            for item in asset.scrape_asset_links():
                asset_num           += 1
                self.total_assets   += 1
                print(f"\n[Asset] #{asset_num} in subcategory #{subcategory_num} | Total: {self.total_assets}")
                try:
                    download    = DownloadAsset([item], self.craftnest.page)
                    download.download_asset()
                    del download
                    gc.collect()
                    self.upload_drive()
                except Exception as e:
                    print(f"[Error] Failed on asset #{asset_num}: {e}")
                    continue
                # Restart browser every N assets to prevent memory crash
                if self.total_assets % BROWSER_RESTART_EVERY == 0:
                    self.restart_browser()
            # Cleanup after every subcategory
            print(f"\n[Subcategory #{subcategory_num}] Finished. Cleaning memory...")
            del asset
            gc.collect()
        print("\n[Main] All subcategories processed successfully!")

    def upload_drive(self):
        """Upload downloaded files to Google Drive and delete local folder"""
        print("[Upload] Uploading to Google Drive...")
        try:
            # Upload to drive
            self.drivedatabase.upload_asset_folder()
            print("[Upload] Upload successful!")
            # Delete local folder after upload
            self.drivedatabase.delete_folder(DOWNLOAD_ASSET_LOCATION)
            print("[Upload] Local folder deleted!")
        except Exception as e:
            print(f"[Upload Error] {e}")

if __name__ == "__main__":
    try:
        m = Main()
        m.download_asset()
    except KeyboardInterrupt:
        print("\nStopped by user. Cleaning up safely...")
    except Exception as e:
        print(f"Error{e}")
    finally:
        gc.collect()