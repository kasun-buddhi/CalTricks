import gc
from data_scraper.CraftNest import CraftNest
from data_scraper.SubCategory import SubCategory
from data_scraper.Asset import Asset
from data_scraper.DownloadAsset import DownloadAsset
from data_scraper.DataScraper import DataScraper
from drive.DriveDataBase import DriveDataBase
from Config import *


class Main:
    def __init__(self):
        self.craftnest      = CraftNest()
        self.drivedatabase  = DriveDataBase(DOWNLOAD_ASSET_LOCATION)
        self.total_assets   = 0
        self.subcategory    = None
        self.asset          = None


    def restart_browser(self):
        """
        Kill entire Chromium + Node.js process and start fresh.
        Also updates subcategory and asset page references to new browser.
        """
        print(f"[Browser] Restarting after {self.total_assets} assets...")
        try:
            self.craftnest.close()
        except Exception as e:
            print(f"[Browser] Error during close: {e}")
        gc.collect()
        self.craftnest      = CraftNest()
        self.craftnest.save_auth()
        self.drivedatabase  = DriveDataBase(DOWNLOAD_ASSET_LOCATION)
        if self.subcategory:
            self.subcategory.page = self.craftnest.page
        if self.asset:
            self.asset.page       = self.craftnest.page
        print("[Browser] Restarted successfully!\n")


    def run(self):
        """
        Main pipeline: for each asset →
            1. Download zip  → get exact folder path (last_download_dir)
            2. Scrape data   → save into that exact folder
            3. Upload to Drive + delete local
        """
        category_links      = self.craftnest.scrape_categories()
        fourth_category     = [category_links[3]]
        self.subcategory    = SubCategory(fourth_category, self.craftnest.page)
        subcategory_num     = 0
        for sub_urls in self.subcategory.scrape_sub_categories():
            subcategory_num += 1
            print(f"\n[Subcategory] Processing #{subcategory_num}")
            self.asset      = Asset(sub_urls, self.craftnest.page)
            asset_num       = 0
            for item in self.asset.scrape_asset_links():
                asset_num         += 1
                self.total_assets += 1
                print(f"\n[Asset] #{asset_num} in subcategory #{subcategory_num} | Total: {self.total_assets}")
                try:
                    # Step 1: Download zip — grab exact folder path after download
                    download = DownloadAsset([item], self.craftnest.page)
                    download.download_asset()
                    last_dir = download.last_download_dir   # ← exact folder path
                    del download
                    gc.collect()
                    # Step 2: Skip scraping if download failed
                    if last_dir is None:
                        print(f"[Skip] Download failed, skipping scrape for: {item}")
                        continue
                    # Step 3: Open fresh page on same context (keeps session/cookies)
                    self.craftnest.page         = self.craftnest.context.new_page()
                    if self.subcategory:
                        self.subcategory.page   = self.craftnest.page
                    if self.asset:
                        self.asset.page         = self.craftnest.page
                    # Step 4: Scrape — pass exact folder path directly, no searching
                    scraper                     = DataScraper([item], self.craftnest.page, last_dir)
                    scraper.scrape_data()
                    del scraper
                    gc.collect()
                    # Step 5: Upload to Drive + delete local
                    self.upload_drive()
                except Exception as e:
                    print(f"[Error] Failed on asset #{asset_num}: {e}")
                    continue
                if self.total_assets % BROWSER_RESTART_EVERY == 0:
                    self.restart_browser()
            print(f"\n[Subcategory #{subcategory_num}] Finished. Cleaning memory...")
            del self.asset
            self.asset = None
            gc.collect()
        print("\n[Main] All subcategories processed successfully!")


    def upload_drive(self):
        """Upload downloaded files to Google Drive and delete local folder."""
        print("[Upload] Uploading to Google Drive...")
        try:
            self.drivedatabase.upload_asset_folder()
            self.drivedatabase.delete_folder(DOWNLOAD_ASSET_LOCATION)
        except Exception as e:
            print(f"[Upload Error] {e}")


if __name__ == "__main__":
    try:
        m = Main()
        m.run()
    except KeyboardInterrupt:
        print("\n[Stopped] Script stopped by user.")
    except Exception as e:
        print(f"{e}")
    finally:
        gc.collect()
        print("Exit")