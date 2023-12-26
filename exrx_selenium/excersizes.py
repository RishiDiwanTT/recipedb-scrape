from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from dataclasses import dataclass
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from queue import Queue, Empty
from urllib import parse


@dataclass
class ScrapeRequest:
    url: str


class Scraper:
    MAX_THREADS = 2
    start_urls = []
    valid_domains = []

    def __init__(self) -> None:
        self._visited_urls = set()
        self.result_data = Queue()

    def should_scrape_url(self, url: str) -> bool:
        url = url.split("#", 1)[0]
        if url in self._visited_urls:
            return False
        result = parse.urlparse(url)

        for domain in self.valid_domains:
            if domain in result.netloc:
                break
        else:
            return False

        return True

    def make_driver(self):
        raise NotImplementedError()

    def parse(self, driver, url):
        raise NotImplementedError()

    def begin(self):
        requests: Queue[ScrapeRequest] = Queue()
        drivers: Queue[webdriver.Chrome] = Queue()
        futures = set()
        executor = ThreadPoolExecutor(
            max_workers=self.MAX_THREADS, thread_name_prefix="Driver"
        )
        for url in self.start_urls:
            requests.put(ScrapeRequest(url))

        for _ in range(self.MAX_THREADS):
            drivers.put(self.make_driver())

        def completion(future: Future):
            if future.done():
                _driver, _requests, _results = future.result()
                drivers.put(_driver)
                print("Drivers:", drivers.qsize())
                for r in _requests:
                    requests.put(r)
                for r in _results:
                    self.result_data.put(r)

        driver = None
        request = None

        while True:
            try:
                # Do we have more requests or drivers available?
                if not driver:
                    driver = drivers.get(timeout=1)
                if not request:
                    request = requests.get(timeout=1)
            except Empty:
                if len(futures):
                    # No, but we have futures pending, wait for atleast one
                    completed = next(as_completed(futures))
                    completion(completed)
                    futures.remove(completed)
                    # One future completed, attempt more requests
                    continue
                else:
                    # no Futures are pending, exit the loop
                    break

            if not self.should_scrape_url(request.url):
                print("Already visited, skipping...", request.url)
                request = None
                continue

            print(request)
            # Get the next available driver and record the URL

            self._visited_urls.add(request.url)

            # Submit to the executor
            future = executor.submit(self._begin_thread, driver, request)
            futures.add(future)

            # Reset the vars
            request = None
            driver = None
            future = None

            time.sleep(0.25)
            print("Queue Size", requests.qsize())
            print("In Progress", len(futures))

        self.parse_results()

    def _begin_thread(self, driver, request) -> tuple:
        requests = []
        results = []
        try:
            driver.get(request.url)
            for item in self.parse(driver, request.url):
                if type(item) is ScrapeRequest:
                    if self.should_scrape_url(item.url):
                        requests.append(item)
                    else:
                        print("Already visited", request.url)
                else:
                    results.append(item)
        except Exception as e:
            print("Exception during parse", request.url, e)
        return driver, requests, results


class EXRXExcersizeScraper(Scraper):
    MAX_THREADS = 3
    valid_domains = ["exrx.net"]
    start_urls = ["https://exrx.net/Lists/Directory"]
    # start_urls = [
    #     "https://exrx.net/WeightExercises/Sternocleidomastoid/CBNeckRotationBelt",
    #     "https://exrx.net/WeightExercises/Sternocleidomastoid/LVNeckFlx",
    # ]

    def make_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        # options.add_argument("user-data-dir=/tmp/exrx-selenium")
        driver = webdriver.Chrome(options=options)
        # driver.timeouts.page_load = 1
        return driver

    def parse(self, driver, url):
        elements = driver.find_elements(by=By.CSS_SELECTOR, value="h2")
        if len(elements) > 0 and any(
            filter(lambda x: x.text == "Classification", elements)
        ):
            # An excersize page
            print("Excersize Page", url)
            yield self._parse_excersize(driver)

        elements = driver.find_elements(by=By.CSS_SELECTOR, value="h1.page-title")
        if len(elements) == 1 and "Exercise" in elements[0].text:
            # Directory Page
            print("Directory", elements[0].text)
            all_links = driver.find_elements(by=By.CSS_SELECTOR, value="#mainShell a")
            for link in all_links:
                href = link.get_attribute("href")
                if href:
                    next_url = href.split("#", 1)[0]
                    yield ScrapeRequest(next_url)

    def _parse_excersize(self, driver):
        data = {}
        article = driver.find_element(by=By.CSS_SELECTOR, value="main>article")
        table = article.find_element(By.CSS_SELECTOR, ".row table")
        classification_eles = table.find_elements(By.TAG_NAME, "td")

        data["name"] = driver.find_element(By.CSS_SELECTOR, "h1.page-title").text
        data["url"] = driver.current_url

        name = None
        for clsf in classification_eles:
            if name is None:
                name = clsf.text
            else:
                data[name] = clsf.text
                name = None

        col2 = article.find_element(By.CSS_SELECTOR, ".row div.col-sm-6:nth-child(2)")
        h2_muscles = None
        target = None
        for element in col2.find_elements(By.CSS_SELECTOR, "h2,p,ul"):
            if element.text == "Muscles":
                h2_muscles = element
            elif h2_muscles and element.tag_name == "p":
                target = element.find_element(By.TAG_NAME, "strong")
                data[target.text] = []
            elif target is not None and element.tag_name == "ul":
                atags = element.find_elements(By.TAG_NAME, "a")
                if not atags:
                    if litags := element.find_elements(By.TAG_NAME, "li"):
                        data[target.text] = [litags[0].text]
                else:
                    for atag in atags:
                        data[target.text].append(atag.text)

        return data

    def parse_results(self):
        with open("exrx.net.ndjson", "w") as fp:
            try:
                while result := self.result_data.get_nowait():
                    print(result)
                    fp.write(json.dumps(result))
                    fp.write("\n")
            except Empty:
                pass


if __name__ == "__main__":
    EXRXExcersizeScraper().begin()
