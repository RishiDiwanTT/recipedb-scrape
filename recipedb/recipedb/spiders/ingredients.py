import json
from typing import List
import scrapy
import logging

logging.getLogger("scrapy.core.scraper").setLevel(logging.INFO)


class IngredientsSpider(scrapy.Spider):
    name = "ingredients"
    allowed_domains = ["cosylab.iiitd.edu.in"]
    BASE_URL = "https://cosylab.iiitd.edu.in/recipedb"

    def start_requests(self):
        for category in [
            "Additive",
            "Bakery",
            "Beverage",
            "Beverage-Alcoholic",
            "Cereal",
            "Condiment",
            "Dairy",
            "Dish",
            "Essential Oil",
            "Fish",
            "Flower",
            "Fruit",
            "Fungi",
            "Herb",
            "Legume",
            "Maize",
            "Meat",
            "Nuts and Seeds",
            "Plant",
            "Plant Derivative",
            "Seafood",
            "Spice",
            "Vegetable",
        ]:
            yield self._create_category_request(category, 1, _initial_page=True)

    def _create_category_request(self, category, page_num, _initial_page=False):
        formdata = dict(
            page=str(page_num),
            autocomplete_category=category,
            autocomplete_noncategory="",
        )
        print("Category request:", formdata)
        return scrapy.FormRequest(
            f"{self.BASE_URL}/search_recipe",
            formdata=formdata,
            cb_kwargs=dict(
                _initial_page=_initial_page,
                category=category,
            ),
        )

    def parse(self, response, _initial_page=False, category=None):
        buttons: List[scrapy.Selector] = response.xpath(
            "//table[@id='myTable']//tr/td[8]/button"
        )
        for button in buttons:
            onclick = button.attrib.get("onclick")
            onclick_data = onclick[16:-1]
            data = json.loads(onclick_data)
            yield (data)

        if _initial_page:
            pages: List[scrapy.Selector] = response.css("a.page-link")
            max_num = 0
            for page in pages:
                try:
                    page_num = int(page.css("::text")[0].get())
                    max_num = max(page_num, max_num)
                except ValueError as ex:
                    pass

            if max_num:
                for num in range(2, max_num):
                    yield self._create_category_request(category, num)
