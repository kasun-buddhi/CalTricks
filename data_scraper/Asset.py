import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Config import *


class Asset:
    def __init__(self, sub_category_links,page) :
        self.sub_category_links     = sub_category_links
        self.page                   = page
    
    def _extract_folder_name(self,sub_category_url):
        # Extract the relevant part from URL
        # Example: https://craftnest.net/collections/cliparts/afro-american-clipart?sort_by=a-z
            # Returns: cliparts/afro_american_clipart
            #print(sub_category_url)
            if "/collections/" in sub_category_url:
                clean_sub_url   =  sub_category_url.split("?")[0]
                parts           = clean_sub_url.split("/collections/")[-1].split('/')
                if len(parts)  >= 2:
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
        file_path       = os.path.join(download_dir, download.suggested_filename)
        # Check if file already exists
        if os.path.exists(file_path):
            print(f"Already exists, skipping: {download.suggested_filename}")
            return None
        # Save the file
        download.save_as(file_path)
        print(f"Saved the file : {file_path}")
        return file_path

    def _save_links_to_json(self, url, status="pending"):
        file_path   = "links.json"
        # Create JSON file if it doesn't exist
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                json.dump({"links": []}, f, indent=4)
        # Load existing data
        with open(file_path, "r") as f:
            data = json.load(f)
        # Add the new link(s)
        if isinstance(url, list):
            for u in url:
                data["links"].append({"url": u, "status": status})
        else:
            data["links"].append({"url": url, "status": status})
        # Save back
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
        link_count = len(url) if isinstance(url, list) else 1
    


    
    def download_asset(self):
        download_button_selector  = "body>main>section>section>div>div>div:nth-child(2)>div:nth-child(4)>a"
        zip_download_selector     = "body>div>div" 
        new_download_selector     = "body>astro-island>div>div>div:nth-child(1)>div:nth-child(2)>div>div>nav>ol>li>button>span"
        processed_urls            = set()
        download_asset_links      = []
        print(f"Received {len(self.sub_category_links)} sub-categories to download")
        for sub_category_url, asset_list in self.sub_category_links.items():
            folder_path      = self._extract_folder_name(sub_category_url)
            download_dir     = os.path.join(DOWNLOAD_ASSET_LOCATION, folder_path)
            os.makedirs(download_dir, exist_ok=True)
            # Remove duplicates
            unique_assets    = [url for url in asset_list if url not in processed_urls]
            print(f"\nSub-category     : {sub_category_url}")
            print(f"Download location  : {download_dir}")
            print(f"Total assets       : {len(asset_list)} (Unique: {len(unique_assets)})")
            for idx, asset_url in enumerate(unique_assets, start=1):
                print(f"[{idx}/{len(unique_assets)}] Downloading asset: {asset_url}")
                try:
                    # Navigate to asset page
                    self.page.goto(asset_url, wait_until="domcontentloaded", timeout=180000)
                    # Click download button
                    self.page.locator(download_button_selector).click()
                    # Wait for the new page if it opens
                    with self.page.context.expect_page() as new_page_info:
                        new_page = new_page_info.value
                    new_page.set_default_timeout(120000)
                    # Close old page safely
                    self.page.close()
                    self.page = new_page
                    # Wait for actual download link/button
                    new_page.wait_for_selector(new_download_selector, timeout=180000)
                    new_page.locator(new_download_selector).click()
                    # Start download and wait
                    with new_page.expect_download(timeout=300000) as download_info:
                        new_page.locator(zip_download_selector).click()
                    download        = download_info.value
                    saved_file      = self._save_file_local(download, download_dir)
                    if saved_file is None:
                        print(f"Failed to save file for: {asset_url}")
                        download_asset_links.append({"url": asset_url, "status": "failed"})
                        continue
                    print(f"Completed download asset: {asset_url}")
                    download_asset_links.append({"url": asset_url, "status": "done"})
                    processed_urls.add(asset_url)
                except Exception as e:
                    print(f"Error downloading {asset_url}: {e}")
                    download_asset_links.append({"url": asset_url, "status": "failed"})
                    continue
            print(f"Completed all assets for sub-category: {sub_category_url}")
            # Save links to JSON after each sub-category
            for item in download_asset_links:
                self._save_links_to_json(item["url"], item["status"])