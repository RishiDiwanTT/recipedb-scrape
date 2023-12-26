# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import json
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem


class RecipedbPipeline:
    def open_spider(self, spider):
        self.file = open("recipedb.ndjson", "w")
        self._recipes_seen = set()
    
    def close_spider(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        print ("PIPLINE", item.get("Recipe_title"))
        if item["Recipe_id"] in self._recipes_seen:
            raise DropItem(f"Already saved {item['Recipe_title']}")
        self.file.write(json.dumps(item))
        self.file.write("\r\n")
        return item
