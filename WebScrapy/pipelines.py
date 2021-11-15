import re
from datetime import datetime

import dataclasses
from unidecode import unidecode

import pymongo
from itemadapter import ItemAdapter
from WebScrapy.items import RawNewsItem, NewsItem
from WebScrapy.utils import process_upload_time


class WebscrapyPipeline:
    collection_name = 'raw_crawled_news'

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item: RawNewsItem, spider) -> NewsItem:

        title: str = item.raw_title
        area_m2: str = item.raw_square
        description: str = item.raw_description

        num_list = list(map(int, re.findall(r'\d+', item.raw_price)))
        price: int = num_list[0] if len(num_list) else None

        location: str = item.raw_location.replace('xem bản đồ', '')
        phone_number: str = item.raw_phone_number.replace('nhấn để hiện số: ', '')

        # news_type in set('ca_nhan', 'moi_gioi')
        news_type: str = item.raw_upload_time[1]
        upload_time: datetime = process_upload_time(item.raw_upload_time[3])

        upload_person: str = None
        if item.raw_upload_person is not None and 'tin rao khác của' in item.raw_upload_person:
            upload_person: str = item.raw_upload_person.replace('tin rao khác của', '').strip()

        news_item = NewsItem(
            title=title,
            price=price,
            area_m2=area_m2,
            description=description,
            upload_time=upload_time,
            location=location,
            upload_person=upload_person,
            phone_number=phone_number,
            news_type=news_type
        )

        detail_info: dict = {}
        # process detail information about apartment
        for info in item.raw_info:
            if ':' in info:
                key = info.split(':')[0].strip()
                # remove accent
                key = unidecode(key)
                key = key.replace(' ', '_')

                value = info.split(':')[-1].strip()

                detail_info[key] = value
            else:
                key = unidecode(info.strip())
                key = key.replace(' ', '_')
                detail_info[key] = True

        self.db[self.collection_name].insert_one({**dataclasses.asdict(news_item), **detail_info})

        return news_item


if __name__ == '__main__':
    mongo_db = 'realestate'
    client = pymongo.MongoClient('mongodb://root:aiLAMTHO123@127.0.0.1:27017')
    db = client[mongo_db]

    print(1)