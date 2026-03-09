import os
import gc
from data_scraper.CraftNest import CraftNest
from data_scraper.SubCategory import SubCategory
from data_scraper.Asset import Asset
from data_scraper.DownloadAsset import DownloadAsset
from data_scraper.DataScraper import DataScraper
from drive.DriveDataBase import DriveDataBase
from googleapiclient.discovery import build
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
        # Update page references so old objects use new browser page
        if self.subcategory:
            self.subcategory.page = self.craftnest.page
        if self.asset:
            self.asset.page = self.craftnest.page
        print("[Browser] Browser restarted successfully! Continuing...\n")

    def _ensure_drive_service(self):
        """Authenticate and ensure Drive service is ready."""
        if not self.drivedatabase.service:
            creds                      = self.drivedatabase._authenticate()
            self.drivedatabase.service = build("drive", "v3", credentials=creds)

    def _process_download_mode(self, item):
        """
        DOWNLOAD_ASSET = True
        Download zip + scrape data into same local folder → upload to Drive.
        """
        print(f"  [Mode] Download + Scrape")

        # Step 1: Download zip
        download     = DownloadAsset([item], self.craftnest.page)
        download.download_asset()
        download_dir = getattr(download, 'last_download_dir', None)
        del download
        gc.collect()

        if not download_dir:
            print(f"  [Skip] Download failed, no folder created")
            return

        # Step 2: Scrape data into same folder
        scraper = DataScraper([item], self.craftnest.page)
        scraper.scrape_data(download_dir=download_dir)
        del scraper
        gc.collect()

        # Step 3: Upload everything to Drive
        self.upload_drive()

    def _process_scrape_only_mode(self, item):
        """
        DOWNLOAD_ASSET = False
        Scrape data only → find existing asset folder on Drive by name → upload into it.
        If folder doesn't exist on Drive → skip, don't create.
        """
        print(f"  [Mode] Scrape only")
        asset_url, sub_url = item

        # Step 1: Scrape data locally
        scraper           = DataScraper([item], self.craftnest.page)
        sub_category_path = scraper._extract_folder_name(sub_url)
        scraper.scrape_data()
        download_dir      = getattr(scraper, 'last_download_dir', None)
        del scraper
        gc.collect()

        if not download_dir or not os.path.exists(download_dir):
            print(f"  [Skip] No local folder created")
            return

        # Step 2: Find matching folder on Drive by folder name
        folder_name = os.path.basename(download_dir)  # e.g. 01_I Floral Alphabet Clipart Bundle
        self._ensure_drive_service()
        drive_folder_id = self.drivedatabase.find_asset_folder_by_name(folder_name, sub_category_path)

        if not drive_folder_id:
            print(f"  [Skip] '{folder_name}' not found on Drive — skipping")
            self.drivedatabase.delete_folder(download_dir)
            return

        # Step 3: Upload data.json, thumbnail, images into existing Drive folder
        self.drivedatabase.upload_scrape_data(download_dir, drive_folder_id)
        self.drivedatabase.delete_folder(download_dir)
        print(f"  [Done] Scrape data uploaded to existing Drive folder")

    def process_asset(self, item, asset_num, subcategory_num):
        """
        Process a single asset.
        Controlled by DOWNLOAD_ASSET flag in Config.
        """
        try:
            if DOWNLOAD_ASSET:
                self._process_download_mode(item)
            else:
                self._process_scrape_only_mode(item)
        except Exception as e:
            print(f"[Error] Failed on asset #{asset_num} in subcategory #{subcategory_num}: {e}")

    def download_asset(self):
        self.category_links = self.craftnest.scrape_categories()
        second_category     = [self.category_links[1]]
        self.subcategory    = SubCategory(second_category, self.craftnest.page)
        # self.subcategory  = SubCategory(self.category_links, self.craftnest.page)
        subcategory_num     = 0

        print(f"[Config] DOWNLOAD_ASSET = {DOWNLOAD_ASSET}")

        for sub_urls in self.subcategory.scrape_sub_categories():
            subcategory_num += 1
            print(f"\n[Subcategory] Processing #{subcategory_num}")

            # Store as instance variable so restart_browser can update page ref
            self.asset = Asset(sub_urls, self.craftnest.page)
            asset_num  = 0

            for item in self.asset.scrape_asset_links():
                asset_num         += 1
                self.total_assets += 1
                print(f"\n[Asset] #{asset_num} in subcategory #{subcategory_num} | Total: {self.total_assets}")

                self.process_asset(item, asset_num, subcategory_num)

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
        """Upload downloaded files to Google Drive and delete local folder."""
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