import re
import dataclasses
from typing import List
from datetime import datetime

import pymongo
from unidecode import unidecode
from scrapy import Spider
from WebScrapy.items import ChoTotRawNewsItem, HomedyRawNewsItem, AlonhadatRawNewsItem
from WebScrapy.items import ChototNewsItem, HomedyNewsItem, AlonhadatNewsItem
from WebScrapy.utils import process_upload_time


class ChototPipeline:
    collection_name = 'nam_test'

    def process_item(self, item: ChoTotRawNewsItem, spider: Spider) -> ChototNewsItem:

        title: str = item.raw_title
        area_m2: str = item.raw_square
        description: str = item.raw_description

        num_list = [float(word.replace(',', '.')) for word in item.raw_price.split(' ') if word.isdigit() or ',' in word]
        price: float = num_list[0] if len(num_list) else None

        location: str = item.raw_location.replace('xem bản đồ', '') if item.raw_location is not None else None
        raw_phone_number = item.raw_phone_number
        phone_number: str = raw_phone_number.replace('nhấn để hiện số: ', '') if raw_phone_number is not None else None

        # news_type in set('ca_nhan', 'moi_gioi')
        news_type: str = item.raw_upload_time[1]
        upload_time: datetime = process_upload_time(item.raw_upload_time[3])

        upload_person: str = None
        if item.raw_upload_person is not None and 'tin rao khác của' in item.raw_upload_person:
            upload_person: str = item.raw_upload_person.replace('tin rao khác của', '').strip()

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

        news_item = ChototNewsItem(
            title=title,
            price=price,
            area_m2=area_m2,
            description=description,
            upload_time=upload_time,
            location=location,
            upload_person=upload_person,
            phone_number=phone_number,
            news_type=news_type,
            url=item.url
        )

        spider.logger.info("Save crawled info of {} to database".format(news_item.url))
        try:
            spider.db[self.collection_name].insert_one({**dataclasses.asdict(news_item), **detail_info})
        except:
            spider.db[self.collection_name].replace_one({'url': news_item.url},
                                                        {**dataclasses.asdict(news_item), **detail_info})
            spider.logger.info("Item is updated in the database")

        return news_item


class HomedyPipeline:
    collection_name = 'nam_test'

    def process_item(self, item: HomedyRawNewsItem, spider: Spider) -> HomedyNewsItem:

        title: str = item.title
        num_list = [float(word.replace(',', '.')) for word in item.raw_price.split(' ') if word.isdigit() or ',' in word]
        price: float = num_list[0] if len(num_list) else None

        area_m2: str = item.raw_area.replace('m2', '').strip() if item.raw_area is not None else None
        description = item.description

        upload_time: datetime = process_upload_time(item.raw_upload_time)
        expire_time: str = item.expire_time
        location: str = item.location

        upload_person: str = item.upload_person
        phone_number: str = item.phone_number

        furniture: List[str] = item.furniture
        convenient: List[str] = item.convenient

        project: str = item.project
        investor: str = item.investor
        status: str = item.status
        url: str = item.url

        news_item = HomedyNewsItem(
            title=title,
            price=price,
            area_m2=area_m2,
            description=description,
            upload_time=upload_time,
            expire_time=expire_time,
            location=location,
            upload_person=upload_person,
            phone_number=phone_number,
            furniture=furniture,
            convenient=convenient,
            project=project,
            investor=investor,
            status=status,
            url=url
        )
        spider.logger.info("Save crawled info of {} to database".format(news_item.url))
        try:
            spider.db[self.collection_name].insert_one(dataclasses.asdict(news_item))
        except:
            # spider.db[self.collection_name].replace_one({'url': news_item.url},
            #                                            dataclasses.asdict(news_item))
            spider.logger.info("Item is updated in the database")

        return news_item

class AlonhadatPipeline:
    collection_name = 'nam_test'

    def process_item(self, item: AlonhadatRawNewsItem, spider: Spider) -> AlonhadatNewsItem:

        title: str = item.raw_title
        area_m2: str = item.raw_square
        description: str = item.raw_description

        num_list = [float(word.replace(',', '.')) for word in item.raw_price.split(' ') if word.isdigit() or ',' in word]
        price: float = num_list[0] if len(num_list) else None

        location: str = item.raw_location.replace('xem bản đồ', '') if item.raw_location is not None else None
        raw_phone_number = item.raw_phone_number
        phone_number: str = raw_phone_number.replace('nhấn để hiện số: ', '') if raw_phone_number is not None else None

        # news_type in set('ca_nhan', 'moi_gioi')
        news_type: str = item.raw_upload_time[1]
        upload_time: datetime = process_upload_time(item.raw_upload_time[3])

        upload_person: str = None
        if item.raw_upload_person is not None and 'tin rao khác của' in item.raw_upload_person:
            upload_person: str = item.raw_upload_person.replace('tin rao khác của', '').strip()

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

        news_item = AlonhadatNewsItem(
            title=title,
            price=price,
            area_m2=area_m2,
            description=description,
            upload_time=upload_time,
            location=location,
            upload_person=upload_person,
            phone_number=phone_number,
            news_type=news_type,
            url=item.url
        )

        spider.logger.info("Save crawled info of {} to database".format(news_item.url))
        try:
            spider.db[self.collection_name].insert_one({**dataclasses.asdict(news_item), **detail_info})
        except:
            spider.db[self.collection_name].replace_one({'url': news_item.url},
                                                        {**dataclasses.asdict(news_item), **detail_info})
            spider.logger.info("Item is updated in the database")

        return news_item


if __name__ == '__main__':
    mongo_db = 'realestate'
    """
    client = pymongo.MongoClient(host='127.0.0.1:27017',
                                 username='webscrapy',
                                 password='68f539388f66a374908f3df559eb4ea2',
                                 authSource='realestate',
                                 authMechanism='SCRAM-SHA-1')
    """
    client = pymongo.MongoClient()

    db = client[mongo_db]

    print(1)