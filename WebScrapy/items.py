from typing import Optional, List
from datetime import datetime

from dataclasses import dataclass


@dataclass
class RawNewsItem:
    raw_title: Optional[str]
    raw_price: Optional[str]
    raw_square: Optional[str]
    raw_description: Optional[str]
    raw_upload_time: Optional[str]
    raw_location: Optional[str]
    raw_upload_person: Optional[str]
    raw_phone_number: Optional[str]
    raw_info: Optional[List[str]]


@dataclass
class NewsItem:
    title: Optional[str]
    price: Optional[int]
    area_m2: Optional[str]
    description: Optional[str]
    upload_time: Optional[datetime]
    location: Optional[str]
    upload_person: Optional[str]
    phone_number: Optional[str]
    # 'ca nhan' or 'moi gioi'
    news_type: Optional[str]

