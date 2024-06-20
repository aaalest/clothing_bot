from kwldn_bot import XBot

from config import config
from handlers.commands import commands_router
from handlers.processing import processing_router

bot = XBot(config.bot.token)

bot.router.include_routers(commands_router, processing_router)

