from data_scraper.CraftNest import CraftNest
from data_scraper.SubCategory import SubCategory
from data_scraper.Asset import Asset


craft = CraftNest()

# All classes reuse the same browser + same page
sub         = SubCategory(craft)
asset       = Asset(craft)
asset_links = asset.setup()