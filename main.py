from data_scraper.CraftNest import CraftNest
from data_scraper.Asset import Asset

craft = CraftNest()
asset = Asset(craft)
asset.download_asset()