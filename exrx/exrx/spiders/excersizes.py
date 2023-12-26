import scrapy

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-GB,en;q=0.9",
    "Sec-Ch-Ua": '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Linux"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

class ExcersizesSpider(scrapy.Spider):
    name = "excersizes"
    # allowed_domains = ["exrx.net"]
    # start_urls = ["https://exrx.net/Lists/Directory"]

    def start_requests(self):
        yield scrapy.Request("https://exrx.net/Lists/Directory", headers=HEADERS)
        # yield scrapy.Request("https://eni1apxttv84b.x.pipedream.net", headers=HEADERS)
        

    def parse(self, response):
        print ("PARSE")
        links = response.xpath("div[@id='mainShell']//a")
        print ("LINKS", links)
        for link in links:
            print (link)
