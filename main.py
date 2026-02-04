import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) 
from data_scraper.CraftNest import CraftNest
url     = "https://craftnest.net/collections/cliparts"
site    = CraftNest()
site.scrape_categories()