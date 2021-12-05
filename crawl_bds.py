import scrapy
import pymongo
from selenium import webdriver
import dataclasses

from scrapy.crawler import CrawlerProcess
from WebScrapy.utils import normalize_text
from datetime import datetime
from typing import List
from scrapy.utils.project import get_project_settings
from WebScrapy.items import BatDongSanNewsItem
import logging
from WebScrapy.utils import process_upload_time, timedelta
from selenium.webdriver.remote.remote_connection import LOGGER
from urllib3.connectionpool import log

log.setLevel(logging.WARNING)
LOGGER.setLevel(logging.WARNING)

class crawl_bds():

    name = 'batdongsan'
    allowed_domains = ['batdongsan.com.vn']

    mongo_db = {
        'HOSTNAME': 'phamvanhanh.ddns.net:8020',
        'USERNAME': 'webscrapy',
        'PASSWORD': '68f539388f66a374908f3df559eb4ea2',
        'DATABASE': 'realestate'
    }
    def __init__(self):

        self.current_page = 1
        self.start_urls = ['https://batdongsan.com.vn/cho-thue-can-ho-chung-cu-ha-noi/p{}'.format(self.current_page)]
        options = webdriver.ChromeOptions()
        #options.add_argument("headless")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        desired_capabilities = options.to_capabilities()
        self.driver = webdriver.Chrome('C:/Users/hands/Downloads/chromedriver_win32/chromedriver.exe', desired_capabilities=desired_capabilities)
        self.collection_name = 'nam_test_bds'

        try:
            self.connection = pymongo.MongoClient(host=self.mongo_db['HOSTNAME'],
                                                  username=self.mongo_db['USERNAME'],
                                                  password=self.mongo_db['PASSWORD'],
                                                  authSource=self.mongo_db['DATABASE'],
                                                  authMechanism='SCRAM-SHA-1')
            self.db = self.connection[self.mongo_db['DATABASE']]
            print('connect successfully')
        except:
            print("Can't connect database")
            self.__del__()

    def __del__(self):
        print("Close connection to database")
        self.connection.close()

    def extract(self, num_page=200):

        for i in range(1, num_page, 1):
            print("Spider {} ,current page: {}".format(self.name, i))

            news_url_list = []
            self.driver.get('https://batdongsan.com.vn/cho-thue-can-ho-chung-cu-ha-noi/p{}'.format(i))
            search_bar = self.driver.find_elements_by_css_selector('a.js__product-link-for-product-id')

            size_page = search_bar.__len__()
            for j in range(size_page):
                news_url_list.append(search_bar[j].get_attribute('href'))

            for url in news_url_list:
                news_item = self.parse_info(url)

                try:
                    self.db[self.collection_name].insert_one({**dataclasses.asdict(news_item)})#, **detail_info})
                    print("Save crawled info of {} to database".format(news_item.url))
                except:
                    self.db[self.collection_name].replace_one({'url': news_item.url},
                                                                {**dataclasses.asdict(news_item)})#, **detail_info})
                    print("Item is updated in the database")

    def parse_info(self, url):
        self.driver.get(url)
        title = self.driver.find_elements_by_css_selector('h1.re__pr-title')
        # raw_title: str = title.text
        title = normalize_text(title[0].text)

        cost_square = self.driver.find_elements_by_css_selector('div.re__pr-short-info-item')
        raw_cost = normalize_text(cost_square)
        price = cost_square[0].text.split('\n')[1]
        raw_price = normalize_text(price)
        num_list = [float(word.replace(',', '.')) for word in raw_price.split(' ') if word.isdigit() or ',' in word]
        price: float = num_list[0] if len(num_list) else None

        square =  cost_square[1].text.split('\n')[1]
        area_m2 = normalize_text(square)[:-2].strip()

        room_number =  cost_square[2].text.split('\n')[1]
        room_number = normalize_text(room_number)[:-3]

        description = self.driver.find_elements_by_css_selector('div.re__section-body.re__detail-content')[0].text
        description = normalize_text(description)

        upload_time = self.driver.find_elements_by_css_selector('div.re__pr-short-info-item.js__pr-config-item')[0].text.split('\n')[1]
        upload_time = normalize_text(upload_time)
        upload_time: datetime = process_upload_time(upload_time[11:])


        duration_time = self.driver.find_elements_by_css_selector('div.re__pr-short-info-item.js__pr-config-item')[1].text.split('\n')[1]
        duration_time = normalize_text(duration_time)
        duration_time: datetime = process_upload_time(duration_time[11:])


        location = self.driver.find_elements_by_css_selector('span.re__pr-short-description')[0].text
        location = normalize_text(location)

        phone_number = self.driver.find_elements_by_css_selector('span.phoneEvent')[0].get_attribute('raw')
        phone_number = normalize_text(phone_number)

        upload_person = self.driver.find_elements_by_css_selector('div.re__contact-name.js_contact-name')[0].text
        upload_person = normalize_text(upload_person)

        curr_url: str = self.driver.current_url
        url = normalize_text(curr_url)


        news_item = BatDongSanNewsItem(
            title=title,
            price=price,
            area_m2=area_m2,
            room_number=room_number,
            description=description,
            raw_duration_time=duration_time,
            upload_time=upload_time,
            location=location,
            upload_person=upload_person,
            phone_number=phone_number,
            url=url
        )

        return  news_item

if __name__ == '__main__':
    temp = crawl_bds()
    temp.extract()

