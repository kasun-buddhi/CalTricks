import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) 
from data_scraper.SubCategory import SubCategory
from drive.DriveUploader import DriveUploader
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaFileUpload
from Config import *


class Asset:
    def __init__(self, craftnest):
        self.craftnest              = craftnest
        self.subcategory            = SubCategory(self.craftnest)
        self.browser                = self.craftnest.browser
        self.drive_uploader         = DriveUploader() 
        self.drive_uploader.authenticate()
        self.drive_uploader.service = build("drive", "v3", credentials=self.drive_uploader.authenticate())
    
    def extract_folder_name(self, url):
        # Extract the relevant part from URL
        # Example: https://craftnest.net/collections/cliparts/afro-american-clipart?sort_by=a-z
        # Returns: afro-american-clipart
        if '/collections/' in url:
            # Remove query parameters
            clean_url      = url.split('?')[0]
            # Get the part after /collections/
            parts          = clean_url.split('/collections/')[-1].split('/')
            if len(parts) >= 2:
                # Return last two parts: category/sub-category
                folder_name   = f"{parts[0]}/{parts[1]}"
            elif len(parts)   == 1:
                # Only category
                folder_name    = parts[0]
            else:
                return "unknown"
            return folder_name.replace('-','_')
        return "unknown"

    def _save_file_local(self, download, download_dir):
        """
        Save downloaded file to local directory
        Args:
            download        : Playwright download object
            download_dir    : Target directory path
            Returns:
            str or None     : File path if saved, None if skipped
        """
        file_path = os.path.join(download_dir, download.suggested_filename)
        # Check if file already exists
        if os.path.exists(file_path):
            print(f"Already exists, skipping: {download.suggested_filename}")
            return None
        # Save the file
        download.save_as(file_path)
        print(f"Saved: {file_path}")
        return file_path

    def download_asset(self):
        download_button_selector    = "body>main>section>section>div>div>div:nth-child(2)>div:nth-child(4)>a"
        new_download_selector       = "body>astro-island>div>div>div:nth-child(1)>div:nth-child(2)>div>div>nav>ol>li>button>span"
        zip_download_selector       = "body>div>div"
        # Ensure base folder exists
        os.makedirs(DOWNLOAD_ASSET_LOCATION, exist_ok=True)
        # Iterate over the generator
        for asset_links in self.subcategory.scrape_sub_category():
            print(f"Received {len(asset_links)} sub-categories to download")
            for sub_category_url, asset_list in asset_links.items():
                # Extract category/sub-category path from URL
                folder_path = self.extract_folder_name(sub_category_url)
                # Create full directory path: Asset/cliparts/afro_american_clipart/
                download_dir = os.path.join(DOWNLOAD_ASSET_LOCATION, folder_path)
                os.makedirs(download_dir, exist_ok=True)
                print(f"Sub-category: {sub_category_url}")
                print(f"Download location: {download_dir}")
                print(f"Total assets: {len(asset_list)}")
                for idx, asset_url in enumerate(asset_list, start=1):
                    print(f"[{idx}/{len(asset_list)}] Downloading asset: {asset_url}")
                    try:
                        self.craftnest.page.goto(asset_url, wait_until="domcontentloaded", timeout=180000)
                        self.craftnest.page.locator(download_button_selector).click()
                        old_page = self.craftnest.page
                        with self.craftnest.page.context.expect_page() as new_page_info:
                            new_page = new_page_info.value
                            self.craftnest.page = new_page
                            self.craftnest.page.set_default_timeout(120000)
                        old_page.close()
                        self.craftnest.page.wait_for_selector(new_download_selector, timeout=180000)
                        self.craftnest.page.locator(new_download_selector).click()
                        with self.craftnest.page.expect_download(timeout=300000) as download_info:
                            self.craftnest.page.locator(zip_download_selector).click()
                        download = download_info.value
                        if self._save_file_local(download, download_dir) is None:
                            continue  # File already exists, skip to next
                    except Exception as e:
                        print(f"Error downloading {asset_url}: {e}")
                        continue   
                    print(f"Completed sub-category: {sub_category_url}")
                    try:
                        # Navigate and create folder structure in Drive
                        current_parent_id   = GOOGLE_DRIVE_PARENT_FOLDER_ID
                        # Create main Asset folder
                        main_folder_name    = os.path.basename(DOWNLOAD_ASSET_LOCATION)
                        main_folder_id      = self.drive_uploader.create_folder(main_folder_name, current_parent_id)
                        current_parent_id   = main_folder_id
                        # Create nested folders (e.g., cliparts, then afro_american_clipart)
                        folders             = folder_path.split('/')
                        for folder_name in folders:
                            folder_id            = self.drive_uploader.create_folder(folder_name, current_parent_id)
                            current_parent_id    = folder_id
                        # Upload all files in the download directory
                        for file_name in os.listdir(download_dir):
                            file_path = os.path.join(download_dir, file_name)
                            if os.path.isfile(file_path):
                                self.drive_uploader.upload_asset_folder(file_path, current_parent_id)
                        print(f"Upload completed for: {folder_path}")
                        # Delete local folder after successful upload
                        print(f"Deleting local folder: {download_dir}")
                        self.drive_uploader.delete_local_folder(download_dir)
                    except Exception as e:
                        print(f"Error uploading sub-category {folder_path}: {e}")
                        print("Local files will be kept due to upload error")
            print("All downloads and uploads completed!")
            self.browser.close()