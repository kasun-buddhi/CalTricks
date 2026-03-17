import sys
import os
import re
import datetime
import requests
import json
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Config import *


class DataScraper:
    def __init__(self, asset_links, page, download_dir=None):
        self.asset_links    = asset_links
        self.page           = page
        self.download_dir   = download_dir  # directly from DownloadAsset


    def _save_json(self, data, folder_path):
        """Save scraped data as data.json inside the asset folder."""
        json_path = os.path.join(folder_path, "data.json")
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"Saved: data.json")
        except OSError as e:
            print(f"Could not save data.json: {e}")


    def download_thumbnail_image(self, download_dir):
        """
        Download thumbnail image and save as thumbnail.jpeg inside asset folder.
            download_dir : Full path to asset folder
        """
        thumbnail_selector  = "body>main>section>section>div>div>div:nth-child(1)>div:nth-child(2)>div>div:nth-child(3)"
        try:
            self.page.locator(thumbnail_selector).wait_for(state="visible", timeout=10000)
            img_url         = self.page.locator(f"{thumbnail_selector} img").first.get_attribute("src")
            if not img_url:
                srcset      = self.page.locator(f"{thumbnail_selector} img").first.get_attribute("srcset")
                if srcset:
                    img_url = srcset.strip().split(",")[-1].strip().split(" ")[0]
            if not img_url:
                style       = self.page.locator(thumbnail_selector).get_attribute("style") or ""
                match       = re.search(r"url\(([^)]+)\)", style)
                if match:
                    img_url = match.group(1).strip("'\"")
            if not img_url:
                print("No thumbnail image found")
                return
            if img_url.startswith("//"):
                img_url     = "https:" + img_url
            elif img_url.startswith("/"):
                img_url     = "https://craftnest.net" + img_url
            clean_url       = img_url.split("?")[0]
            response        = requests.get(clean_url, timeout=30)
            response.raise_for_status()
            thumbnail_path  = os.path.join(download_dir, "thumbnail.jpeg")
            with open(thumbnail_path, "wb") as f:
                f.write(response.content)
            print(f"Saved: thumbnail.jpeg")
        except Exception as e:
            print(f"Thumbnail download failed: {e}")


    def download_sample_images(self, download_dir):
        """
        Download all sample images into images/ subfolder inside the asset folder.
            download_dir : Full path to asset folder
        """
        images_selector     = "body>main>section>section>div>div>div:nth-child(1)>div:nth-child(2)>div>div:nth-child(1)>div:nth-child(1)>div"
        images_dir          = os.path.join(download_dir, "images")
        os.makedirs(images_dir, exist_ok=True)
        try:
            self.page.locator(images_selector).first.wait_for(state="visible", timeout=10000)
            img_elements    = self.page.locator(f"{images_selector} img").all()
            if not img_elements:
                print("No sample images found")
                return
            print(f"Sample images found: {len(img_elements)}")
            for idx, img in enumerate(img_elements, start=1):
                try:
                    img_url         = img.get_attribute("src") or img.get_attribute("data-src")
                    if not img_url:
                        print(f"Image {idx}: no src, skipping")
                        continue
                    if img_url.startswith("//"):
                        img_url     = "https:" + img_url
                    elif img_url.startswith("/"):
                        img_url     = "https://craftnest.net" + img_url
                    clean_url       = img_url.split("?")[0]
                    response        = requests.get(clean_url, timeout=30)
                    response.raise_for_status()
                    filename        = f"sample_{idx:02d}.jpeg"
                    image_path      = os.path.join(images_dir, filename)
                    with open(image_path, "wb") as f:
                        f.write(response.content)
                    print(f"Saved: images/{filename}")
                except Exception as e:
                    print(f"Failed image {idx}: {e}")
        except Exception as e:
            print(f"Sample images download failed: {e}")


    def scrape_data(self):
        """
        Scrape metadata, thumbnail, and sample images for each asset.
        Saves into the folder passed directly from DownloadAsset:
            Asset/category/sub_category/0017 3D Inflated Candy.../
                ├── 0017 3D Inflated Candy....zip   ← from DownloadAsset
                ├── data.json
                ├── thumbnail.jpeg
                └── images/
                    ├── sample_01.jpeg
                    └── ...
        """
        title_selector       = "body>main>section>section>div>div>div:nth-child(2)>div:nth-child(3)>h2"
        description_selector = "body>main>section>section>div>div>div:nth-child(2)>div:nth-child(6)>div>div>p"
        include_selector     = "body>main>section>section>div>div>div:nth-child(2)>div:nth-child(7)>div>div>ul"
        tags_selector        = "body>main>section>section>div>div>div:nth-child(2)>div:nth-child(8)>div>div:nth-child(2)>div"
        for i, (asset_url, sub_url) in enumerate(self.asset_links):
            try:
                # Use download_dir passed directly from DownloadAsset — no folder searching
                download_dir = self.download_dir
                if download_dir is None:
                    print(f"[Skip] No download_dir for: {asset_url}")
                    continue
                # Stop if no zip file found in the folder
                zip_files   = [f for f in os.listdir(download_dir) if f.endswith(".zip")]
                if not zip_files:
                    print(f"[Stop] No zip file found in: {download_dir} — stopping scraper.")
                    break
                # Navigate to asset page
                self.page.goto(asset_url, wait_until="domcontentloaded", timeout=180000)
                self.page.wait_for_timeout(2000)
                print(f"Page loaded: {self.page.url}")
                # --- Title ---
                title       = ""
                try:
                    self.page.locator(title_selector).wait_for(state="visible", timeout=30000)
                    title   = self.page.locator(title_selector).first.inner_text().strip()
                    print(f"Title: {title}")
                except Exception:
                    print("Title not found")
                # --- Description ---
                description     = ""
                try:
                    desc_text   = ""
                    try:
                        self.page.locator(description_selector).wait_for(state="visible", timeout=10000)
                        desc_elements   = self.page.locator(description_selector).all()
                        desc_text       = " ".join([el.inner_text().strip() for el in desc_elements])
                    except Exception:
                        print("Description not found")
                    includes_text       = ""
                    try:
                        includes_list   = []
                        for ul in self.page.locator(include_selector).all():
                            if not ul.is_visible():
                                continue
                            items                   = [li.inner_text().strip() for li in ul.locator("li").all() if li.inner_text().strip()]
                            if items and len(items) >= 2:
                                includes_list       = items
                                break
                        includes_text               = " ".join(includes_list)
                    except Exception:
                        print("Includes not found")
                    description     = " ".join(filter(None, [desc_text, includes_text])).strip()
                    print(f"Description: {description[:80]}...")
                except Exception:
                    print("Description block failed")
                # --- Tags ---
                tags                = []
                try:
                    tag_elements    = self.page.locator(tags_selector).all()
                    tags            = [
                        tag.inner_text().strip()
                        for tag in tag_elements
                        if tag.inner_text().strip() and tag.inner_text().strip() != "," ]
                    print(f"Tags: {tags}")
                except Exception:
                    print("Tags not found")
                # --- Build data dict and save ---
                data = {
                    "id"                : i + 1,
                    "title"             : title,
                    "description"       : description,
                    "tags"              : tags,
                    "price"             : "",
                    "source_url"        : asset_url,
                    "download_date_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                self._save_json(data, download_dir)
                self.download_thumbnail_image(download_dir)
                self.download_sample_images(download_dir)
            except Exception as e:
                print(f"[Error] scrape_data failed for {asset_url}: {e}")