import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) 
from data_scraper.CraftNest import CraftNest

class SubCategory:
    def __init__(self):
        self.craftnest  = CraftNest()
        self.page       = None
    
    def setup(self):
        # Get CraftNest ready
        category_links = self.craftnest.scrape_categories()
        self.page = self.craftnest.page
        return category_links

    def scrape_sub_category(self):
        category_links     = self.setup()
        #print(category_links)  
        for link in category_links:
            #print(link)
            self.page.goto(link,wait_until="domcontentloaded")


