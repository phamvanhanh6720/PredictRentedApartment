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

from selenium.webdriver.common.keys import Keys


log.setLevel(logging.WARNING)
LOGGER.setLevel(logging.WARNING)


class BatDongSanSpider:
    name = 'batdongsan'
    allowed_domains = ['batdongsan.com.vn']
    # start_urls = 'https://batdongsan.com.vn/cho-thue-can-ho-chung-cu-ha-noi/p1'
    object_name = 'thue-can-ho-chung-cu'
    cfg = dict(get_project_settings())
    max_cached_request = cfg['MAX_CACHED_REQUEST']
    # num_pages_per_day = cfg['CHOTOT_NUM_PAGES_PER_DAY']
    num_pages_per_day = 2

    def __init__(self):
        self.start_urls = 'https://batdongsan.com.vn/cho-thue-can-ho-chung-cu-ha-noi/p1'
        options = webdriver.ChromeOptions()
        #options.add_argument("headless")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        desired_capabilities = options.to_capabilities()
        self.driver = webdriver.Chrome('C:/Users/Admin/Downloads/chromedriver', desired_capabilities=desired_capabilities)

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
            # self.logger.info("Connect database unsuccessfully")
            self.__del__()

    def __del__(self):
        # self.driver.close()
        # self.logger.info("Close connection to database")
        self.connection.close()



    def parse(self):

        self.driver.get(self.start_urls)
        search_bar = self.driver.find_elements_by_css_selector('a.js__product-link-for-product-id')
        # search_bar.clear()
        # search_bar.send_keys("getting started")
        # search_bar.send_keys(Keys.RETURN)

        news_url_list = []
        size_page = search_bar.__len__()
        for i in range(size_page):
            news_url_list.append(search_bar[i].get_attribute('href'))
        news_url_list



        if len(news_url_list):
            for news_url in news_url_list:
                item = self.driver.get(news_url)
                self.parse_info(item)
                # new_requests.append(scrapy.Request(url=news_url, callback=self.parse_info))

            if self.num_cached_request <= self.max_cached_request and self.current_page <= self.num_pages_per_day:
                self.current_page += 1
                # self.logger.info("Spider {} ,current page: {}".format(self.name, self.current_page))
                next_page = 'https://batdongsan.com.vn/cho-thue-can-ho-chung-cu-ha-noi/p{}'.format(self.current_page)
                # yield scrapy.Request(url=next_page, callback=self.parse)
                self.start_urls = next_page
                self.parse()
            else:
                new_requests = []

        # return new_requests
        search_bar.clear()
        search_bar.send_keys("getting started")
        search_bar.send_keys(Keys.RETURN)
        return search_bar

    def parse_info(self, item):
        title = self.driver.find_elements_by_css_selector('h1.re__pr-title')
        # raw_title: str = title.text
        raw_title = normalize_text(title[0].text)

        cost_square = self.driver.find_elements_by_css_selector('div.re__pr-short-info-item')
        raw_cost = normalize_text(cost_square)

        price = cost_square[0].text.split('\n')[1]
        raw_price = normalize_text(price)

        square =  cost_square[1].text.split('\n')[1]
        raw_square = normalize_text(square)

        description = self.driver.find_elements_by_css_selector('div.re__section-body.re__detail-content')[0].text
        raw_description = normalize_text(description)


        upload_time = self.driver.find_elements_by_css_selector('div.re__pr-short-info-item.js__pr-config-item')[0].text.split('\n')[1]
        raw_upload_time = normalize_text(upload_time)

        duration_time = self.driver.find_elements_by_css_selector('div.re__pr-short-info-item.js__pr-config-item')[1].text.split('\n')[1]
        raw_duration_time = normalize_text(duration_time)

        location = self.driver.find_elements_by_css_selector('span.re__pr-short-description')[0].text
        raw_location = normalize_text(location)

        phone_number = self.driver.find_elements_by_css_selector('span.phoneEvent')[0].get_attribute('raw')
        raw_phone_number = normalize_text(phone_number)

        upload_person = self.driver.find_elements_by_css_selector('div.re__contact-name.js_contact-name')[0].text
        raw_upload_person = normalize_text(upload_person)

        curr_url: str = self.driver.current_url
        raw_url = normalize_text(curr_url)


        raw_news_item = RawNewsItem(
            raw_title=raw_title,
            # raw_duration_time=raw_duration_time,
            raw_price=raw_price,
            raw_location=raw_location,
            raw_description=raw_description,
            raw_square=raw_square,
            raw_upload_time=raw_upload_time,
            raw_phone_number=raw_phone_number,
            raw_upload_person=raw_upload_person,
            url=raw_url,
        )

        yield raw_news_item


if __name__ == '__main__':
    # setting = get_project_settings()
    # process = CrawlerProcess(get_project_settings())
    # process.crawl(BatDongSanSpider)
    # process.start()
    test = BatDongSanSpider()
    test.parse()
    print("test")