import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy_selenium import SeleniumRequest
from selenium import webdriver


class ChototSpider(scrapy.Spider):
    name = 'chotot'
    allowed_domains = ['nha.chotot.com']
    start_urls = ['https://nha.chotot.com/ha-noi/thue-can-ho-chung-cu?page=1']
    object_name = 'thue-can-ho-chung-cu'

    def parse(self, response):
        news_url_list = response.css('li.AdItem_wrapperAdItem__1hEwM a::attr(href)').getall()

        news_url = news_url_list[10]
        news_url: str = news_url.replace('[object Object]', ChototSpider.object_name)
        news_url = response.urljoin(news_url)
        yield SeleniumRequest(url=news_url, callback=self.parse_info)

        if len(news_url_list):
            for news_url in news_url_list:
                news_url: str = news_url.replace('[object Object]', ChototSpider.object_name)
                news_url = response.urljoin(news_url)
                yield scrapy.Request(url=news_url, callback=self.parse_info, meta=meta)

    def parse_info(self, response):
        raw_title: str = response.css('h1.AdDecription_adTitle__2I0VE').get()
        raw_price: str = response.css('span.AdDecription_price__O6z15 span[itemprop]::text').get()
        raw_square: str = response.css('span.AdDecription_squareMetre__2KYh8').get()

        raw_description = response.css('p.AdDecription_adBody__1c8SG::text').get()

        options = webdriver.ChromeOptions()
        options.add_argument("headless")
        desired_capabilities = options.to_capabilities()
        driver = webdriver.Chrome(desired_capabilities=desired_capabilities)

        driver.get(response.url)
        driver.implicitly_wait(3)
        # wait = WebDriverWait(driver, 5)
        # wait.until(EC.presence_of_element_located((By.CLASS_NAME, "fz13")))

        driver.close()


if __name__ == '__main__':

    process = CrawlerProcess()
    process.crawl(ChototSpider)
    process.start()