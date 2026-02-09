import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) 


class SubCategory:
    def __init__(self,category_links,page):
        self.links      = category_links
        self.page       = page

    def __scroll_until_no_new_content(self,page,selector):
            previous_count    = 0
            no_change_count   = 0
            scroll_times      = 10
            for scroll_num in range(scroll_times):
                # Get current count
                #current_count = len(page.query_selector_all(selector))
                page.evaluate("""window.scrollBy({top: window.innerHeight,behavior: 'smooth'});""")
                # Wait 3 seconds after each scroll
                page.wait_for_timeout(3000) 
                # Check new count
                new_count  = len(page.query_selector_all(selector))
                print(f"Scroll {scroll_num + 1}: Items loaded: {new_count}")
                if new_count == previous_count:
                    no_change_count += 1
                    if no_change_count >= 3:
                        print(f"Final count: {new_count}")
                        break
                else:
                    no_change_count = 0
                previous_count = new_count
            return new_count

    def scrape_sub_category(self):
        category_links          = self.links
        asset_link_dict         = {}  
        sub_categories_ul       = "body>main>section>div>div>div>div>div:nth-child(2)>div:nth-child(4)>ul"
        sub_category_items      = sub_categories_ul + " > li > a"
        asset_item_selector     = "body >main> section> div> div> div> div> div:nth-child(4)> div >div:nth-child(2)> div > div"
        for link in category_links:
            print("Visiting category:", link)
            self.page.goto(link, wait_until = "domcontentloaded")
            self.page.wait_for_selector(sub_categories_ul)
            # Reset sub_urls for each main category
            sub_urls = []
            # Get all sub-category links
            sub_elements     = self.page.locator(sub_category_items)
            sub_count        = sub_elements.count()
            print("Total sub-categories found:", sub_count)
            for i in range(sub_count):
                href    = sub_elements.nth(i).get_attribute("href")
                name    = sub_elements.nth(i).inner_text().strip()
                # Make href absolute if needed
                if href.startswith("/"):
                    href    = "https://craftnest.net" + href
                sub_urls.append((name, href))
            #for urls in sub_urls:print(urls)
            # Loop over each sub-category
            for idx, (name, sub_url) in enumerate(sub_urls, start=1):
                print(f"Opening sub-category {idx}/{len(sub_urls)}: {name}")
                print("URL:", sub_url)
                self.page.goto(sub_url, wait_until="domcontentloaded")
                final_count     = self.__scroll_until_no_new_content(self.page, asset_item_selector)
                #print(final_count)
                self.page.wait_for_timeout(1200)
                # Get all assets in this sub-category
                assets = self.page.query_selector_all(asset_item_selector)
                print(" Loaded assets:", len(assets))
                for i, asset in enumerate(assets, start=1):
                    a_tag             = asset.query_selector("a")
                    if a_tag:
                        asset_link    = a_tag.get_attribute("href")
                        # Make full URL
                        full_url      = "https://craftnest.net" + asset_link
                        #print(f"{i}.{full_url}")
                        if sub_url not in asset_link_dict:
                            asset_link_dict[sub_url] = []
                        asset_link_dict[sub_url].append(full_url)
                # Yield after completing entire sub-category
                print(f"Completed sub-category: {sub_url}")
                yield asset_link_dict     