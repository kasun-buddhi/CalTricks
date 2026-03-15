class SubCategory:
    def __init__(self,category_links,page):
        self.links      = category_links
        self.page       = page


    def scrape_sub_categories(self):
        sub_categories_ul       = "body>main>section>div>div>div>div>div:nth-child(2)>div:nth-child(4)>ul"
        sub_category_items      = sub_categories_ul + " > li > a"
        sub_urls                = []
        for link in self.links:
            print("Visiting category:", link)
            if self.page is None or self.page.is_closed():
                self.page       = self.page.context.new_page()
            self.page.goto(link, wait_until = "domcontentloaded")
            self.page.wait_for_selector(sub_categories_ul)
            # Reset sub_urls for each main category
            sub_elements     = self.page.locator(sub_category_items)
            sub_count        = sub_elements.count()
            print("Total sub-categories found:", sub_count)
            for i in range(sub_count):
                href        = sub_elements.nth(i).get_attribute("href")
                name        = sub_elements.nth(i).inner_text().strip()
                # Make href absolute if needed
                if href.startswith("/"):
                    href    = "https://craftnest.net" + href
                sub_urls.append((name, href))
            yield sub_urls   