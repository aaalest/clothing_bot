import asyncio
import logging
import random
import time

import aiohttp
import cv2
import numpy as np
from PIL import Image
from aiogram.types import BufferedInputFile, Message
from typing import Dict, Optional
import base64
import aiogram

from config import config, BackendServer


async def check_backend_availability(backend: BackendServer) -> BackendServer | None:
    async with aiohttp.ClientSession() as session:
        logging.info(f'Checking backend {backend.host}')
        try:
            await session.head(f'http://{backend.host}')
            return backend
        except Exception as e:
            logging.exception(e)


async def get_available_backends() -> list[BackendServer]:
    return [x for x in await asyncio.gather(*[check_backend_availability(x) for x in config.backends]) if x]


async def get_suitable_backend() -> BackendServer | None:
    available_hosts = await get_available_backends()

    # TODO: Write backend suitability algorithm

    return random.choice(available_hosts) if len(available_hosts) else None


async def generate(file_path, bot, backend: BackendServer, document: dict) -> dict:
    now = time.time()
    print(f'document: {document}')

    data: Dict[str, Optional[str]] = {
        "lower": document["options"]["lower"],
        "lower_color": document["options"]["lower_color"],
        "upper": document["options"]["upper"],
        "upper_color": document["options"]["upper_color"],
        "style": document["options"]["style"]
    }

    # for key, value in list(data.items()):
    #     data[key] = data[key].lower()

    print(f'data: {data}')

    download_file = await bot.download_file(file_path)
    print(f'download_file time: {time.time() - now}')

    # open the image and convert it to RGB
    image_np = cv2.cvtColor(np.array(Image.open(download_file)), cv2.COLOR_RGB2BGR)

    now = time.time()

    # Encode the image into a memory buffer
    _, img_encoded = cv2.imencode('.jpg', image_np)

    response = await backend.request_generation(img_encoded.tobytes(), data)

    if "message" not in response:
        response["massage"] = "image"
    if "image" in response:
        # Assuming `generated_photo` is a base64 encoded string
        decoded_photo = base64.b64decode(response["image"])
        response["image"] = BufferedInputFile(decoded_photo, filename='img.jpg')
        print(f'convert img time: {time.time() - now}')
    return response

