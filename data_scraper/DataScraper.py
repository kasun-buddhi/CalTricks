import sys
import os
import gc
import re
import datetime
import requests
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Config import *


class DataScraper:
    """
    Scrapes product data from CraftNest asset pages and saves
    all content locally in a structured folder hierarchy.
    data.json       ← title, description, includes, tags, price, source_url, date
    thumbnail.jpeg  ← main product thumbnail
    images/
    sample_01.jpeg
    sample_02.jpeg
    Args:
        asset_links : list of tuples [(asset_url, sub_category_url), ...]
        page        : Playwright page object (authenticated browser session)
    Methods:
        scrape_data()                          → main entry point, orchestrates all scraping
        download_thumbnail_image(download_dir) → downloads main product thumbnail as thumbnail.jpeg
        download_sample_images(download_dir)   → downloads all sample images into images/ subfolder
        _extract_folder_name(sub_category_url) → converts URL to Asset/category/sub_category path
        _get_asset_folder_name(title, index)   → builds numbered folder name e.g. 01_Asset Name
        _save_json(data, folder_path)          → saves scraped data as data.json
    """
    def __init__(self, asset_links, page):
        self.asset_links    = asset_links 
        self.page           = page


    def _extract_folder_name(self, sub_category_url):
        """
        Extract structured folder path from sub-category URL.
        Example:
            Input  : https://craftnest.net/collections/cliparts/afro-american-clipart?sort_by=a-z
            Output : Asset/cliparts/afro_american_clipart
        """
        if "/collections/" in sub_category_url:
            clean_url           = sub_category_url.split("?")[0]
            parts               = clean_url.split("/collections/")[-1].split("/")
            if len(parts)       >= 2:
                category        = parts[0].replace("-", "_")
                sub_category    = parts[1].replace("-", "_")
                return f"Asset/{category}/{sub_category}"
            elif len(parts) == 1:
                category    = parts[0].replace("-", "_")
                return f"Asset/{category}"
        return "Asset/unknown"


    def _get_asset_folder_name(self, title, index):
        """
        Build numbered asset folder name from page title.
        Example:
            title  : Floral Alphabet Clipart Bundle
            index  : 1
            Returns: 01_Floral Alphabet Clipart Bundle
        """
        stripped_name   = re.sub(r'^\d+_', '', title.strip())
        new_id          = f"{index:02d}"
        return f"{new_id}_{stripped_name}"


    def _save_json(self, data, folder_path):
        """Save scraped data as data.json inside the asset folder."""
        json_path       = os.path.join(folder_path, "data.json")
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent = 4, ensure_ascii = False)
            print(f"  Saved data.json")
        except OSError as e:
            print(f"  [Error] Could not save data.json: {e}")


    def download_thumbnail_image(self, download_dir):
        """
        Download thumbnail image and save as thumbnail.jpeg in asset folder.
            download_dir : Full path to asset folder
        """
        thumbnail_selector      = "body>main>section>section>div>div>div:nth-child(1)>div:nth-child(2)>div>div:nth-child(3)"
        try:
            self.page.locator(thumbnail_selector).wait_for(state="visible", timeout=10000)
            # Try <img> src
            img_url             = self.page.locator(f"{thumbnail_selector} img").first.get_attribute("src")
            # Try srcset fallback
            if not img_url:
                srcset          = self.page.locator(f"{thumbnail_selector} img").first.get_attribute("srcset")
                if srcset:
                    img_url     = srcset.strip().split(",")[-1].strip().split(" ")[0]
            # Try background-image CSS fallback
            if not img_url:
                style       = self.page.locator(thumbnail_selector).get_attribute("style") or ""
                match       = re.search(r"url\(([^)]+)\)", style)
                if match:
                    img_url = match.group(1).strip("'\"")
            if not img_url:
                print("  [Warning] No thumbnail image found")
                return
            # Make URL absolute
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
            print(f"Thumbnail  : thumbnail.jpeg")
        except Exception as e:
            print(f"[Warning] Thumbnail download failed: {e}")


    def download_sample_images(self, download_dir):
        """
        Download all sample images and save into images/ subfolder.
            download_dir : Full path to asset folder
        """
        images_selector     = "body>main>section>section>div>div>div:nth-child(1)>div:nth-child(2)>div>div:nth-child(1)>div:nth-child(1)>div"
        images_dir          = os.path.join(download_dir, "images")
        os.makedirs(images_dir, exist_ok=True)
        try:
            self.page.locator(images_selector).first.wait_for(state="visible", timeout=10000)
            img_elements    = self.page.locator(f"{images_selector} img").all()
            if not img_elements:
                print("  [Warning] No sample images found")
                return
            print(f"  Sample imgs: {len(img_elements)} found")
            for idx, img in enumerate(img_elements, start=1):
                try:
                    img_url = img.get_attribute("src") or img.get_attribute("data-src")
                    if not img_url:
                        print(f"[Warning] Image {idx} has no src, skipping")
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
                    print(f"    Saved: {filename}")
                except Exception as e:
                    print(f"    [Warning] Failed to download image {idx}: {e}")
        except Exception as e:
            print(f"  [Warning] Sample images download failed: {e}")


    def scrape_data(self):
        title_selector          = "h2"
        description_selector    = "[class*='description'] p"
        include_selector        = "[class*='rte'] ul, [class*='description'] ul, [class*='product__description'] ul"
        tags_selector           = "[class*='tag'] span"
        sub_category_counters   = {}
        print(f"Scraping data for {len(self.asset_links)} assets...")
        for i, (asset_url, sub_url) in enumerate(self.asset_links):
            sub_category_path = self._extract_folder_name(sub_url)
            print(f"\n[Asset {i+1}/{len(self.asset_links)}] {asset_url}")
            try:
                self.page.goto(asset_url, wait_until="domcontentloaded", timeout=180000)
                title   = ""
                try:
                    self.page.locator(title_selector).wait_for(state="visible", timeout=15000)
                    title = self.page.locator(title_selector).inner_text().strip()
                except Exception:
                    print("  [Warning] Title not found")
                description = ""
                try:
                    desc_text = ""
                    try:
                        self.page.locator(description_selector).wait_for(state="visible", timeout=10000)
                        desc_elements   = self.page.locator(description_selector).all()
                        desc_text       = " ".join([el.inner_text().strip() for el in desc_elements])
                    except Exception:
                        print("  [Warning] Description text not found")
                    includes_text       = ""
                    try:
                        includes_list   = []
                        for ul in self.page.locator(include_selector).all():
                            if not ul.is_visible():
                                continue
                            items = [li.inner_text().strip() for li in ul.locator("li").all() if li.inner_text().strip()]
                            if items and len(items) >= 2:
                                includes_list = items
                                break
                        includes_text = " ".join(includes_list)
                    except Exception:
                        print("  [Warning] Includes not found")
                    description = " ".join(filter(None, [desc_text, includes_text])).strip()
                except Exception:
                    print("  [Warning] Description not found")
                tags               = []
                try:
                    tag_elements   = self.page.locator(tags_selector).all()
                    tags           = [tag.inner_text().strip() for tag in tag_elements if tag.inner_text().strip()]
                except Exception:
                    print("  [Warning] Tags not found")
                #Build folder 
                sub_category_counters[sub_category_path]  = sub_category_counters.get(sub_category_path, 0) + 1
                asset_index                               = sub_category_counters[sub_category_path]
                asset_folder_name                         = self._get_asset_folder_name(title if title else f"asset_{asset_index}", asset_index)
                download_dir                              = os.path.join(DOWNLOAD_ASSET_LOCATION, sub_category_path, asset_folder_name)
                os.makedirs(download_dir, exist_ok=True)
                #Save JSON 
                data = {
                    "id"                 : i + 1,
                    "title"              : title,
                    "description"        : description,
                    "tags"               : tags,
                    "price"              : "",
                    "source_url"         : asset_url,
                    "download_date_time" : datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                print(f"  Title         : {title}")
                print(f"  Description   : {description[:60]}..." if len(description) > 60 else f"  Description: {description}")
                print(f"  Tags          : {tags}")
                print(f"  Folder        : {download_dir}")
                self._save_json(data, download_dir)
                self.download_thumbnail_image(download_dir)
                self.download_sample_images(download_dir)
            except Exception as e:
                print(f"[Error] Failed on asset {i+1}: {asset_url} -> {e}")
                continue
        print(f"\n[Done] Scraped {len(self.asset_links)} assets.")
        gc.collect()