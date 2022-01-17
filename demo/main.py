import json
import requests
import joblib
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Optional

from cfg import Config


class InputItems(BaseModel):
    furniture_type: int = Field(..., description="0: unknown, 1: full, 2: cơ bản, 3: full cao cấp, 4: nguyên bản")
    apartment_type: int = Field(..., description="0: tập thể, 1: thường, 2: studio, 3: mini, 4: cao cấp")
    news_type: int = Field(..., description='0: môi giới, 1: cá nhân')
    bedroom_number: int
    area: float
    location: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]


def convert_to_coordinates(loc: str, token):
    url = lambda address: 'https://maps.googleapis.com/maps/api/geocode/json?address={}&key={}'.format(address, token)
    latitude = None
    longitude = None

    response = requests.get(url=url(address=loc))
    if response.status_code == 200:
        try:
            coordinates = json.loads(response.text)
            formatted_address = coordinates['results'][0]['formatted_address']
            latitude = coordinates['results'][0]['geometry']['location']['lat']
            longitude = coordinates['results'][0]['geometry']['location']['lng']

        except Exception as e:
            print(e)

    return latitude, longitude


app = FastAPI(title='KHDL API', version='0.1.0')
model = joblib.load('../modeling/model/best_random_forest.joblib')
API_TOKEN = Config.load_config()['API_TOKEN']


@app.post("/predict")
async def predict_price(item: InputItems):
    if isinstance(item.location, str):
        latitude, longitude = convert_to_coordinates(item.location, API_TOKEN)

    data_point = np.array([item.news_type, item.bedroom_number,
                           item.area, item.apartment_type, item.furniture_type,
                           latitude, longitude])

    price = model.predict(data_point.reshape(1, -1))
    price = price[0]
    price = round(price, 1)

    return price