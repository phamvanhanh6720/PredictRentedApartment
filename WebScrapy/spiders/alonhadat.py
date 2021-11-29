from typing import List

import scrapy
import pymongo
from scrapy.crawler import CrawlerProcess

from scrapy.utils.project import get_project_settings
from WebScrapy.items import AlonhadatRawNewsItem

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
        'MAX_CACHED_REQUEST': 2000,
        'MAX_PAGES_PER_DAY': 500,
        'ITEM_PIPELINES': {
            'WebScrapy.pipelines.AlonhadatPipeline': 300
        }
    }
    cfg = dict(get_project_settings())

    def __init__(self):
        super(AlonhadatSpider, self).__init__()
        self.mongo_db = self.cfg['MONGO_SETTINGS']
        self.num_cached_request = 0
        self.current_page = 100

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
            if self.num_cached_request <= max_cached_request and self.current_page >= 1:
                self.current_page -= 1
                self.logger.info("Spider {} ,current page: {}".format(self.name, self.current_page))

                next_page = 'https://alonhadat.com.vn/nha-dat/cho-thue/can-ho-chung-cu/1/ha-noi/trang--{}.html'.format(
                    self.current_page)
                new_requests.append(scrapy.Request(url=next_page, callback=self.parse, meta={'dont_cache': True}))
            else:
                new_requests = []

        return new_requests

    def parse_info(self, response):

        title: str = response.css('div.title h1::text').get()
        raw_price: str = response.css('div.moreinfor span.value::text').get()
        raw_area: str = response.css('div.moreinfor span.square span.value::text').get()
        raw_description: str = response.css('div.detail.text-content::text').get()

        raw_upload_time: str = response.css("div.title span.date::text").get()
        location: str = response.css("div.address span.value::text").get()
        upload_person: str = response.css("div.contact-info div.content div.name::text").get()
        phone_number: str = response.css('div.contact-info div.fone a::text').get().replace('.', '').replace(' ', '')

        raw_info: List[str] = []

        project: str = response.css("span.project a::text").get()
        raw_info: List[str] = response.css("div.moreinfor1 div.infor table td::text").getall()

        raw_news_item = AlonhadatRawNewsItem(
            title=title,
            raw_price=raw_price,
            raw_area=raw_area,
            raw_description=raw_description,
            raw_upload_time=raw_upload_time,
            location=location,
            upload_person=upload_person,
            phone_number=phone_number,
            project=project,
            raw_info=raw_info,
            url=response.url
        )

        return raw_news_item


if __name__ == '__main__':
    setting = get_project_settings()
    process = CrawlerProcess(get_project_settings())
    process.crawl(AlonhadatSpider)
    process.start()