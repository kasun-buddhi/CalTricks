import sys
import os
import gc
import json
import tempfile
import platform
import shutil   
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Config import *


class DownloadAsset:
    def __init__(self, asset_links,page) :
        self.asset_links   = asset_links 
        self.page          = page
    
    def clean_disk(self):
        removed     = 0
        system      = platform.system()
        temp_dir    = Path(tempfile.gettempdir())
        for item in temp_dir.iterdir():
            try:
                if item.is_file() or item.is_symlink():
                    removed += item.stat().st_size
                    item.unlink()
                elif item.is_dir():
                    size       = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                    removed   += size
                    shutil.rmtree(item)
            except Exception:
                continue
        # clean windows temp files
        if system       == "Windows":
            win_temp    =  Path(os.getenv("TEMP", "C:\\Windows\\Temp"))
            for item in win_temp.iterdir():
                try:
                    if item.is_file() or item.is_symlink():
                        removed += item.stat().st_size
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                except Exception:
                    continue
        # clean linux
        elif system     == "Linux":
            unix_temp   =  Path("/tmp")
            for item in unix_temp.iterdir():
                try:
                    if item.is_file() or item.is_symlink():
                        removed += item.stat().st_size
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                except Exception:
                    continue
        print(f"Freed {removed / (1024*1024):.2f} MB.")
            
    def _extract_folder_name(self,sub_category_url):
        # Extract the relevant part from URL
        # Example: https://craftnest.net/collections/cliparts/afro-american-clipart?sort_by=a-z
        # Returns: cliparts/afro_american_clipart
        # print(sub_category_url)
            if "/collections/" in sub_category_url:
                clean_sub_url    =  sub_category_url.split("?")[0]
                parts            = clean_sub_url.split("/collections/")[-1].split('/')
                if len(parts)   >= 2:
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
        file_path        = os.path.join(download_dir, download.suggested_filename)
        # Check if file already exists
        if os.path.exists(file_path):
            print(f"Already exists, skipping: {download.suggested_filename}")
            return None
        # Save the file
        download.save_as(file_path)
        print(f"Saved the file : {file_path}")
        return file_path

    def failed_download_json(self, urls):
        """ save failed download links 
        """
        file_path   = "failed_download.json"
        data        = {"links": []}
        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as f:
                    content     = f.read().strip()
                    if content:
                        data    = json.loads(content)
            except json.JSONDecodeError:
                print("[Warning] Corrupted JSON detected, backing up and starting fresh...")
                backup  = file_path.replace(".json", "_corrupted_backup.json")
                os.replace(file_path, backup)
                data    = {"links": []}
                existing_urls = {entry["url"] for entry in data["links"]}
        if isinstance(urls, list):
            for u in urls:
                if u not in existing_urls:
                    data["links"].append({"url": u})
        else:
            if urls not in existing_urls:
                data["links"].append({"url": urls})
        try:
            tmp_path = file_path + ".tmp"
            with open(tmp_path, "w") as f:
                json.dump(data, f, indent = 4)
            os.replace(tmp_path, file_path)
        except OSError:
            print("could not save failed downloads!")
    
    def download_asset(self):
        # Clean disk at start of every batch
        self.clean_disk()
        download_button_selector    = "body>main>section>section>div>div>div:nth-child(2)>div:nth-child(4)>a"
        zip_download_selector       = "body>div>div"
        new_download_selector       = "body>astro-island>div>div>div:nth-child(1)>div:nth-child(2)>div>div>nav>ol>li>button>span"
        processed_urls              = set()
        context                     = self.page.context
        print(f"Downloading {len(self.asset_links)} assets...")
        for i, (asset_url, sub_url) in enumerate(self.asset_links):
            folder_path     = self._extract_folder_name(sub_url)
            download_dir    = os.path.join(DOWNLOAD_ASSET_LOCATION, folder_path)
            os.makedirs(download_dir, exist_ok=True)
            print(f"\n[Asset {i+1}/{len(self.asset_links)}] {asset_url}")
            print(f"[Location] {download_dir}")
            new_page    = None
            download    = None
            try:
                if self.page is None or self.page.is_closed():
                    self.page = context.new_page()
                self.page.goto(asset_url, wait_until="domcontentloaded", timeout=180000)
                with context.expect_page(timeout=60000) as new_page_info:
                    self.page.locator(download_button_selector).click()
                new_page = new_page_info.value
                new_page.set_default_timeout(120000)
                self.page.close()
                self.page = new_page
                new_page.wait_for_selector(new_download_selector, timeout=180000)
                new_page.locator(new_download_selector).click()
                with new_page.expect_download(timeout=300000) as download_info:
                    new_page.locator(zip_download_selector).click()
                download   = download_info.value
                saved_file = self._save_file_local(download, download_dir)
                if saved_file is None:
                    self.failed_download_json([asset_url])
                    continue
                processed_urls.add(asset_url)
            except Exception as e:
                print(f"[Error] Download failed: {asset_url} -> {e}")
                self.failed_download_json([asset_url])
            finally:
                #  Close all pages 
                for p in [new_page, self.page]:
                    try:
                        if p and not p.is_closed():
                            p.close()
                    except Exception:
                        pass
                # Clear references
                new_page     = None
                download     = None
                self.page    = None
                #Force garbage collection after every asset
                gc.collect()
            # Clean disk every 5 assets to free temp files
            if (i + 1) % 5 == 0:
                print(f"[Memory] Running cleanup at asset {i+1}")
                self.clean_disk()
                gc.collect()
        print(f"Processed {len(processed_urls)}/{len(self.asset_links)} assets.")
        processed_urls.clear()
        gc.collect()