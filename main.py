from data_scraper.CraftNest import CraftNest
from data_scraper.SubCategory import SubCategory
from data_scraper.Asset import Asset


craft       = CraftNest()
sub         = SubCategory(craft)
asset       = Asset(craft)
#asset_links = asset.setup()
asset.download_asset()