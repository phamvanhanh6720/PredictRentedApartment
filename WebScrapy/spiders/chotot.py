import scrapy
import pymongo
from selenium import webdriver
from scrapy.crawler import CrawlerProcess
from typing import List

from scrapy.utils.project import get_project_settings
from WebScrapy.items import RawNewsItem
from WebScrapy.utils import normalize_text

import logging
from selenium.webdriver.remote.remote_connection import LOGGER
from urllib3.connectionpool import log


log.setLevel(logging.WARNING)
LOGGER.setLevel(logging.WARNING)


class ChototSpider(scrapy.Spider):
    name = 'chotot'
    allowed_domains = ['nha.chotot.com']
    start_urls = ['https://nha.chotot.com/ha-noi/thue-can-ho-chung-cu?page=1']
    object_name = 'thue-can-ho-chung-cu'
    cfg = dict(get_project_settings())
    max_cached_request = cfg['MAX_CACHED_REQUEST']
    num_pages_per_day = cfg['CHOTOT_NUM_PAGES_PER_DAY']

    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument("headless")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        desired_capabilities = options.to_capabilities()
        self.driver = webdriver.Chrome(desired_capabilities=desired_capabilities)

        self.mongo_db = self.cfg['MONGO_SETTINGS']
        self.num_cached_request = 0
        self.current_page = 1

        try:
            self.connection = pymongo.MongoClient(host=self.mongo_db['HOSTNAME'],
                                                  username=self.mongo_db['USERNAME'],
                                                  password=self.mongo_db['PASSWORD'],
                                                  authSource=self.mongo_db['DATABASE'],
                                                  authMechanism='SCRAM-SHA-1')
            self.db = self.connection[self.mongo_db['DATABASE']]
            self.logger.info("Connect database successfully")
        except:
            self.logger.info("Connect database unsuccessfully")
            self.__del__()

    def __del__(self):
        self.driver.close()
        self.logger.info("Close connection to database")
        self.connection.close()

    def parse(self, response):

        news_url_list = response.css('li.AdItem_wrapperAdItem__1hEwM a::attr(href)').getall()
        new_requests = []

        if len(news_url_list):
            for news_url in news_url_list:
                news_url: str = news_url.replace('[object Object]', ChototSpider.object_name)
                news_url = response.urljoin(news_url)

                # yield scrapy.Request(url=news_url, callback=self.parse_info)
                new_requests.append(scrapy.Request(url=news_url, callback=self.parse_info))

            if self.num_cached_request <= self.max_cached_request and self.current_page <= self.num_pages_per_day:
                self.current_page += 1
                self.logger.info("Spider {} ,current page: {}".format(self.name, self.current_page))
                next_page = 'https://nha.chotot.com/ha-noi/thue-can-ho-chung-cu?page={}'.format(self.current_page)
                # yield scrapy.Request(url=next_page, callback=self.parse)
                new_requests.append(scrapy.Request(url=next_page, callback=self.parse))
            else:
                new_requests = []

        return new_requests

    def parse_info(self, response):
        raw_title: str = response.css('h1.AdDecription_adTitle__2I0VE::text').getall()[-1]
        raw_title = normalize_text(raw_title)

        raw_price: str = response.css('span.AdDecription_price__O6z15 span[itemprop]::text').get()
        raw_price = normalize_text(raw_price)

        raw_square: str = response.css('span.AdDecription_squareMetre__2KYh8::text').getall()[1]
        raw_square = normalize_text(raw_square)

        raw_description: str = response.css('p.AdDecription_adBody__1c8SG::text').get()
        raw_description = normalize_text(raw_description)

        raw_upload_time: List[str] = response.css("span.AdImage_imageCaptionText__39oDK::text").getall()
        raw_upload_time = [normalize_text(_) for _ in raw_upload_time]

        self.driver.get(response.url)
        self.driver.implicitly_wait(4)

        raw_location: str = None
        info_elements: str = None
        raw_info: List[str] = []
        raw_upload_person: str = None
        raw_phone_number: str = None
        try:
            raw_location = self.driver.find_element_by_class_name("fz13").text
            raw_location = normalize_text(raw_location)

            info_elements = self.driver.find_elements_by_class_name("AdParam_adMediaParam__3bzmC")
            for ele in info_elements:
                raw_info.append(normalize_text(ele.text))

            raw_phone_number = self.driver.find_elements_by_tag_name('linkcontact')[-1].text
            raw_phone_number = normalize_text(raw_phone_number)

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            self.driver.implicitly_wait(2)
            raw_upload_person = self.driver.find_element_by_class_name("SimilarAds_similarAdsTitle__3MuV7").text
            raw_upload_person = normalize_text(raw_upload_person)
        except:
            pass

        raw_news_item = RawNewsItem(
            raw_title=raw_title,
            raw_info=raw_info,
            raw_price=raw_price,
            raw_location=raw_location,
            raw_description=raw_description,
            raw_square=raw_square,
            raw_upload_time=raw_upload_time,
            raw_phone_number=raw_phone_number,
            raw_upload_person=raw_upload_person,
            url=response.url
        )

        yield raw_news_item


if __name__ == '__main__':
    setting = get_project_settings()
    process = CrawlerProcess(get_project_settings())
    process.crawl(ChototSpider)
    process.start()