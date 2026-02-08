from data_scraper.CraftNest import CraftNest
from data_scraper.Asset import Asset
from drive.DriveUploader import DriveUploader

craft = CraftNest()
asset = Asset(craft)
#asset.download_asset()

uploader = DriveUploader()
uploader.upload_asset_folder()