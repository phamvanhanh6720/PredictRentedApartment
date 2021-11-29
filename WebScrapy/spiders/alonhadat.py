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
    custom_settings = {
        'HTTPCACHE_EXPIRATION_SECS': 43200,
        'MAX_CACHED_REQUEST': 500,
        'MAX_PAGES_PER_DAY': 25,
        'ITEM_PIPELINES': {
            'WebScrapy.pipelines.HomedyPipeline': 300
        }
    }
    cfg = dict(get_project_settings())

    def __init__(self):
        super(AlonhadatSpider, self).__init__()
        self.mongo_db = self.cfg['MONGO_SETTINGS']
        self.num_cached_request = 0
        self.current_page = 1

        self.start_urls = ['https://alonhadat.com.vn/nha-dat/cho-thue/can-ho-chung-cu/1/ha-noi/trang--{}.html'.format(
            self.current_page)]

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
        self.logger.info("Close connection to database")
        self.connection.close()

    def parse(self, response):

        news_url_list: List[str] = response.css('div#content-body div#left div.content-item div.ct_title a::attr(href)').getall()
        new_requests = []

        if len(news_url_list):
            for i in range(len(news_url_list)):
                news_url = news_url_list[i]
                news_url: str = response.urljoin(news_url)

                new_requests.append(scrapy.Request(url=news_url, callback=self.parse_info))

            max_cached_request = self.settings.attributes['MAX_CACHED_REQUEST'].value
            max_pages_per_day = self.settings.attributes['MAX_PAGES_PER_DAY'].value
            if self.num_cached_request <= max_cached_request and self.current_page <= max_pages_per_day:
                self.current_page += 1
                self.logger.info("Spider {} ,current page: {}".format(self.name, self.current_page))

                next_page = 'https://alonhadat.com.vn/nha-dat/cho-thue/can-ho-chung-cu/1/ha-noi/trang--{}.html'.format(
                    self.current_page)
                new_requests.append(scrapy.Request(url=next_page, callback=self.parse, meta={'dont_cache': True}))
            else:
                new_requests = []

        return new_requests

    def parse_info(self, response):
        pass
        raw_title: str = response.css('div.property div.title h1::text').get()
        raw_price: str = response.css('div.property div.moreinfor span.price span.value::text').get()
        raw_area: str = response.css('div.property div.moreinfor span.square span.value::text').get()
        raw_description: str = response.css('div.property div.detail.text-content::text').get()

        raw_upload_time: str = response.css('div.property div.title span.date::text').get()
        location: str = response.css('div.property div.address span.value::text').get()
        upload_person: str = response.css('div#right div.contact-info div.content div.name::text').get()






if __name__ == '__main__':
    setting = get_project_settings()
    process = CrawlerProcess()
    process.crawl(AlonhadatSpider)
    process.start()