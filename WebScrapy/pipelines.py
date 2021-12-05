import requests
import dataclasses
from typing import List
from datetime import datetime
import pymongo

from bs4 import BeautifulSoup
from unidecode import unidecode
from scrapy import Spider
from WebScrapy.items import ChoTotRawNewsItem, HomedyRawNewsItem, AlonhadatRawNewsItem, BatDongSanRawNewsItem, \
    BatDongSanNewsItem
from WebScrapy.items import ChototNewsItem, HomedyNewsItem, AlonhadatNewsItem
from WebScrapy.utils import process_upload_time, timedelta


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
    collection_name = 'nam_test_1'

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
            spider.db[self.collection_name].replace_one({'url': news_item.url},
                                                        dataclasses.asdict(news_item))
            spider.logger.info("Item is updated in the database")

        return news_item


class AlonhadatPipeline:
    collection_name = 'nam_test'

    def process_item(self, item: AlonhadatRawNewsItem, spider: Spider) -> AlonhadatNewsItem:

        def extract_upload_time(raw_upload_time: str):
            current_time: datetime = datetime.now()
            result: datetime = datetime.now()

            if 'hôm nay' in raw_upload_time:
                result = current_time
            elif 'hôm qua' in raw_upload_time:
                result = current_time - timedelta(days=1)

            try:
                upload_date = raw_upload_time.replace('ngày đăng:', '').strip()
                date: str = upload_date.split('/')[0]
                month: str = upload_date.split('/')[1]
                year: str = upload_date.split('/')[-1][-2:]
                result = datetime.strptime('{}/{}/{} 00:00:00'.format(date, month, year), '%d/%m/%y %H:%M:%S')
            except:
                pass

            return result

        title: str = item.title
        num_list = [float(word.replace(',', '.')) for word in item.raw_price.split(' ') if word.isdigit() or ',' in word]
        price: float = num_list[0] if len(num_list) else None
        area_m2: str = item.raw_area[:-1].strip()
        description: str = item.raw_description

        upload_time: datetime = extract_upload_time(item.raw_upload_time)
        location: str = item.location
        upload_person: str = item.upload_person
        phone_number: str = item.phone_number

        project: str = item.project

        detail_info: dict = {}
        raw_info = item.raw_info

        # process detail information about apartment
        fix_attrs = ['ma_tin', 'huong', 'phong_an', 'loai_tin', 'duong_truoc_nha', 'nha_bep',
                     'loai_bds', 'phap_ly', 'san_thuong', 'chieu_ngang', 'so_lau', 'cho_de_xe_hoi',
                     'chieu_dai', 'so_phong_ngu', 'chinh_chu']
        i = 0
        while True:
            key = raw_info[min(i, len(raw_info) - 1)]
            value = raw_info[min(i+1, len(raw_info) - 1)]
            # remove accent
            if i >= len(raw_info):
                break

            key = unidecode(key)
            key = key.replace(' ', '_')
            temp_value = unidecode(value).replace(' ', '_')
            if key in fix_attrs and temp_value not in fix_attrs:
                i += 2
                if '_' in value or '-' in value:
                    continue
                detail_info[key] = value

            elif key == temp_value:
                break
            else:
                detail_info[key] = True
                i += 1

        id_post: str = detail_info['ma_tin'].strip()
        url_request = 'https://alonhadat.com.vn/handler/Handler.ashx?command=35&propertyid={}&captcha='.format(id_post)
        headers = {
            "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
            "Origin": 'https://alonhadat.com.vn',
            "Referer": item.url
        }

        sub_response = requests.get(url=url_request, timeout=5, headers=headers)

        if sub_response.status_code == 200:
            phone_number_element: str = sub_response.text
            soup = BeautifulSoup(phone_number_element, 'html.parser')
            a_tag = soup.find('a')
            if a_tag is not None:
                phone_number = a_tag.string.replace('.', '')

        news_item = AlonhadatNewsItem(
            title=title,
            price=price,
            area_m2=area_m2,
            description=description,
            upload_time=upload_time,
            location=location,
            upload_person=upload_person,
            phone_number=phone_number,
            project=project,
            url=item.url
        )

        spider.logger.info("Save crawled info of {} to database".format(news_item.url))
        try:
            spider.db[self.collection_name].insert_one({**dataclasses.asdict(news_item), **detail_info})
        except:
            # spider.db[self.collection_name].replace_one({'url': news_item.url},
            #                                             {**dataclasses.asdict(news_item), **detail_info})
            spider.logger.info("Item is updated in the database")

        return news_item

class BatDongSanPipeline:
    collection_name = 'test_bat_dong_san'

    def process_item(self, item: BatDongSanRawNewsItem, spider: Spider) -> BatDongSanNewsItem:

        title: str = item.raw_title
        num_list = [float(word.replace(',', '.')) for word in item.raw_price.split(' ') if word.isdigit() or ',' in word]
        price: float = num_list[0] if len(num_list) else None
        area_m2: str = item.raw_area[:-1].strip()
        room_number: str = item.raw_room_number
        description: str = item.raw_description

        raw_duration_time: datetime = process_upload_time(item.raw_duration_time[11:])
        upload_time: datetime = process_upload_time(item.raw_upload_time[11:])
        location: str = item.raw_location
        upload_person: str = item.raw_upload_person
        phone_number: str = item.raw_phone_number

        news_item = BatDongSanNewsItem(
            title=title,
            price=price,
            area_m2=area_m2,
            room_number=room_number,
            description=description,
            raw_duration_time=raw_duration_time,
            upload_time=upload_time,
            location=location,
            upload_person=upload_person,
            phone_number=phone_number,
            url=item.url
        )

        spider.logger.info("Save crawled info of {} to database".format(news_item.url))
        try:
            spider.db[self.collection_name].insert_one({**dataclasses.asdict(news_item)})#, **detail_info})
        except:
            spider.db[self.collection_name].replace_one({'url': news_item.url},
                                                        {**dataclasses.asdict(news_item)})#, **detail_info})
            spider.logger.info("Item is updated in the database")

        return news_item

        # spider.logger.info("Save crawled info of {} to database".format(news_item.url))
        # try:
        #     spider.db[self.collection_name].insert_one(dataclasses.asdict(news_item))
        # except:
        #     spider.db[self.collection_name].replace_one({'url': news_item.url},
        #                                                 dataclasses.asdict(news_item))
        #     spider.logger.info("Item is updated in the database")
        #
        # return news_item

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