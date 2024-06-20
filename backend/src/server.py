import asyncio

import uvicorn
from fastapi import FastAPI

from config import config
from routes.processing import processing_router

app = FastAPI(
    title='Stable diffusion clothing API'
)

app.include_router(processing_router)


@app.head('/')
def test_head():
    return {'type': 'success'}


async def start():
    server_config = uvicorn.Config('server:app', host='0.0.0.0', port=config.server.port, log_level='info')
    server = uvicorn.Server(server_config)
    await server.serve()
    await asyncio.Event().wait()
