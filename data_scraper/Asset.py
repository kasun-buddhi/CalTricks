import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) 
from   data_scraper.SubCategory import SubCategory

class Asset:
    def __init__(self,craftnest):
        self.craftnest      = craftnest
        self.subcategory    = SubCategory(self.craftnest)
        self.page           = None
    
    def setup(self):
        asset_links         = self.subcategory.scrape_sub_category()
        self.page           = self.craftnest.page
        return asset_links
    