import scrapy
import pymongo
from selenium import webdriver
from scrapy.crawler import CrawlerProcess
from typing import List

from scrapy.utils.project import get_project_settings
from WebScrapy.items import HomedyRawNewsItem
from WebScrapy.utils import normalize_text

import logging
from selenium.webdriver.remote.remote_connection import LOGGER
from urllib3.connectionpool import log


log.setLevel(logging.WARNING)
LOGGER.setLevel(logging.WARNING)


class HomedySpider(scrapy.Spider):
    name = 'homedy'
    allowed_domains = ['homedy.com']

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
        super(HomedySpider, self).__init__()

        self.mongo_db = self.cfg['MONGO_SETTINGS']
        self.num_cached_request = 0
        self.current_page = 25
        self.start_urls = ['https://homedy.com/cho-thue-can-ho-ha-noi/p{}'.format(self.current_page)]

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

        def filter_phone_number(raw_info: str):
            phone_number: str = raw_info.split(',')[1]
            phone_number = phone_number.replace("'", "+").replace('+', '')

            return phone_number

        def filter_full_name(raw_info: str):
            full_name: str = raw_info.split(',')[2]
            full_name = full_name.replace("'", "+").replace('+', '')

            return full_name

        news_url_list: List[str] = response.css('div.product-item-top h3 a::attr(href)').getall()
        raw_person_info: List[str] = response.css('div.product-item-top div.box-price-agency span.btn-list-chat').getall()

        phone_number_list: List[str] = list(map(filter_phone_number, raw_person_info))
        full_name_list: List[str] = list(map(filter_full_name, raw_person_info))

        raw_price_list: List[str] = response.css('div.product-item-top span.price::text').getall()
        raw_area_m2: List[str] = response.css('div.product-item-top span.acreage::text').getall()
        address_list: List[str] = response.css('div.product-item-top li.address::attr(title)').getall()

        report: List[str] = response.css('div.report p::text').getall()
        new_requests = []

        if len(report):
            return new_requests

        if len(news_url_list):
            for i in range(len(news_url_list)):
                news_url = news_url_list[i]
                news_url: str = response.urljoin(news_url)
                data: dict = {
                    'phone_number': phone_number_list[i],
                    'full_name': full_name_list[i],
                    'raw_price': raw_price_list[i],
                    'raw_area': raw_area_m2[i],
                    'address': address_list[i]

                }
                new_requests.append(scrapy.Request(url=news_url, callback=self.parse_info, cb_kwargs=data))

            max_cached_request = self.settings.attributes['MAX_CACHED_REQUEST'].value
            max_pages_per_day = self.settings.attributes['MAX_PAGES_PER_DAY'].value
            if self.num_cached_request <= max_cached_request and self.current_page >= 1:
                self.current_page -= 1
                self.logger.info("Spider {} ,current page: {}".format(self.name, self.current_page))

                next_page = 'https://homedy.com/cho-thue-can-ho-ha-noi/p{}'.format(self.current_page)
                new_requests.append(scrapy.Request(url=next_page, callback=self.parse, meta={'dont_cache': True}))
            else:
                new_requests = []
            pass

        return new_requests

    def parse_info(self, response, **kwargs):

        phone_number: str = kwargs['phone_number']
        upload_person: str = kwargs['full_name']
        location: str = kwargs['address']
        raw_price: str = kwargs['raw_price']
        raw_area: str = kwargs['raw_area']

        url: str = response.url

        title: str = response.css('div.product-detail-top-left h1::text').get()
        upload_info: List[str] = response.css('div.product-info span::text').getall()

        raw_upload_time = [element for element in upload_info if 'đăng' in normalize_text(element)]
        raw_upload_time: str = raw_upload_time[0] if len(raw_upload_time) else None

        raw_expire_time = [element for element in upload_info if '/' in normalize_text(element)]
        expire_time: str = raw_expire_time[0] if len(raw_expire_time) else None

        project: str = response.css('div.info a.name::text').get()
        investor: str = response.css('div.info span.title-invertor::text').get()
        status: str = response.css('div.info p span.text-title::text').get()

        description_list: List[str] = response.css('div.description.readmore p::text').getall()
        description = '\n'.join(description_list)
        furniture: List[str] = response.css('div.utilities-detail.furniture div.item div.title::text').getall()
        convenient: List[str] = response.css('div.utilities-detail.convenient div.item div.title::text').getall()

        raw_news_item = HomedyRawNewsItem(title=title,
                                          raw_price=raw_price,
                                          raw_area=raw_area,
                                          description=description,
                                          raw_upload_time=raw_upload_time,
                                          location=location,
                                          upload_person=upload_person,
                                          phone_number=phone_number,
                                          expire_time=expire_time,
                                          furniture=furniture,
                                          project=project,
                                          investor=investor,
                                          convenient=convenient,
                                          status=status,
                                          url=url)

        return raw_news_item


if __name__ == '__main__':
    setting = get_project_settings()
    process = CrawlerProcess(setting)
    process.crawl(HomedySpider)
    process.start()