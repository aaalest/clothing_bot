import asyncio
import logging

from bot import bot
from config import config
import collection

from handlers.commands import start


logging.basicConfig(level=logging.DEBUG if config.bot.debug else logging.INFO)


async def main():
    # await connect(config.bot.mongo, config.bot.database, [User])
    collection.update_collections()
    await bot.start()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
