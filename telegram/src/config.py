import aiohttp
from pydantic import BaseModel
import json
import os.path
from typing import TypeVar
import urllib

data_path = os.path.join(r'data')
config_file = os.path.join(data_path, 'config.json')

if not os.path.exists(data_path):
    os.mkdir(data_path)


class BotSettings(BaseModel):
    token: str = ''
    owners: list[int] = []
    mongo: str = ''
    debug: bool = True
    database_name: str = ''


class BasicBotConfig(BaseModel):
    bot: BotSettings = BotSettings()

    def __init__(self):
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                super().__init__(**json.load(f))
        else:
            super().__init__()

        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.model_dump(), f, ensure_ascii=True, sort_keys=True, indent=4)


R = TypeVar('R')


class BackendServer(BaseModel):
    name: str
    host: str
    priority: float
    vram: int

    async def request_generation(self, image: bytes, processing_data: dict[str, str]):
        # Correctly encode the dictionary into query parameters without nesting under 'data'
        query_string = urllib.parse.urlencode(processing_data)
        # Append the query string directly to the URL
        url = f'http://{self.host}/processing/upload?{query_string}'
        print(f'URL: {url}')
        data = aiohttp.FormData()
        # Append the image to the form data
        data.add_field('image',
                       image,
                       filename='image.jpeg',
                       content_type='image/jpeg')
        # Make the POST request with the image and parameters
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as resp:
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 400:
                    return {"status": "failure", "message": "clothing not found"}
                else:
                    return {"status": "failure", "message": "unknown error"}


class ClothingBotConfig(BasicBotConfig):
    backends: list[BackendServer] = []


config = ClothingBotConfig()
