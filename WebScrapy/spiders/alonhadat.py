import scrapy
import pymongo
from selenium import webdriver
from scrapy.crawler import CrawlerProcess
from typing import List

from scrapy.utils.project import get_project_settings
from WebScrapy.items import AlonhadatRawNewsItem
from WebScrapy.utils import normalize_text

import logging
from selenium.webdriver.remote.remote_connection import LOGGER
from urllib3.connectionpool import log


log.setLevel(logging.WARNING)
LOGGER.setLevel(logging.WARNING)


class AlonhadatSpider(scrapy.Spider):
    name = 'alonhadat'
    allowed_domains = ['alonhadat.com.vn']
    cfg = dict(get_project_settings())

    custom_settings = {
        'HTTPCACHE_EXPIRATION_SECS': 3600,
        'MAX_CACHED_REQUEST': 500,
        'MAX_PAGES_PER_DAY': 50,
        'ITEM_PIPELINES': {
            'WebScrapy.pipelines.AlonhadatPipeline': 300
        }
    }

    def __init__(self):
        options = webdriver.ChromeOptions()
        #options.add_argument("headless")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        desired_capabilities = options.to_capabilities()
        self.driver = webdriver.Chrome('C:/Users/hands/Downloads/chromedriver_win32/chromedriver.exe')

        self.mongo_db = self.cfg['MONGO_SETTINGS']
        self.num_cached_request = 0
        self.current_page = 50
        self.start_urls = ['https://alonhadat.com.vn/nha-dat/cho-thue/can-ho-chung-cu/trang--{}.html'.format(self.current_page)]

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

        news_url_list = response.css('div.ct_title a::attr(href)').getall()
        new_requests = []

        if len(news_url_list):
            for news_url in news_url_list:
                news_url = response.urljoin(news_url)

                new_requests.append(scrapy.Request(url=news_url, callback=self.parse_info))

            max_cached_request = self.settings.attributes['MAX_CACHED_REQUEST'].value
            max_pages_per_day = self.settings.attributes['MAX_PAGES_PER_DAY'].value
            if self.num_cached_request <= max_cached_request and self.current_page >= 1:
                self.current_page -= 1
                self.logger.info("Spider {} ,current page: {}".format(self.name, self.current_page))
                next_page = 'https://alonhadat.com.vn/nha-dat/cho-thue/can-ho-chung-cu/trang--{}.html'.format(self.current_page)
                new_requests.append(scrapy.Request(url=next_page, callback=self.parse, meta={'dont_cache': True}))
            else:
                new_requests = []

        return new_requests

    def parse_info(self, response):
        raw_title: str = response.css('div.title h1::text').get()

        raw_price: str = response.css('div.moreinfor span.value::text').get()
        raw_price = normalize_text(raw_price)

        raw_area: str = response.css('div.moreinfor span.square span.value::text').get()
        raw_area = normalize_text(raw_area)

        raw_description: str = response.css('div.detail.text-content::text').get()
        raw_description = normalize_text(raw_description)

        raw_upload_time: str = response.css("div.title span.date::text").get()
        raw_upload_time = normalize_text(raw_upload_time)

        raw_location: str = response.css("div.address span.value::text").get()
        raw_location = normalize_text(raw_location)

        raw_upload_person: str = response.css("div.contact-info div.content div.name::text").get()
        raw_upload_person = normalize_text(raw_upload_person)

        raw_phone_number: str = response.css("div.contact-info div.content div.fone a::text").get()
        raw_phone_number = normalize_text(raw_phone_number)

        self.driver.get(response.url)
        self.driver.implicitly_wait(4)

        raw_infor: List[str] = []
        raw_project: str = None
        try:
            raw_project = response.css("span.project a::text").get()
            raw_project = normalize_text(raw_project)
            list = response.css("div.moreinfor1 div.infor table tr td::text").getall()
            for i in list:
                raw_infor.append(i)
        except:
            pass
        raw_news_item = AlonhadatRawNewsItem(
            raw_title=raw_title,
            raw_price=raw_price,
            raw_area=raw_area,
            raw_description=raw_description,
            raw_upload_time=raw_upload_time,
            raw_location=raw_location,
            raw_upload_person=raw_upload_person,
            raw_phone_number=raw_phone_number,
            raw_project=raw_project,
            raw_info=raw_infor,
            url=response.url
        )

        return raw_news_item


if __name__ == '__main__':
    setting = get_project_settings()
    process = CrawlerProcess(get_project_settings())
    process.crawl(AlonhadatSpider)
    process.start()