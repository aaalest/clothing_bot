import time

from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram import Router, Bot, F, Dispatcher
from aiogram.exceptions import TelegramNetworkError
import asyncio
import logging

import utils
import collection
from translate import tr, languages
from ..processing.process_image import handlers as processing_handlers

start_router = Router()


@start_router.callback_query()
async def keyboard_callback_handler(callback_query: types.CallbackQuery):
    print(callback_query)
    callback_query_data = callback_query.data.split(': ')
    handlers = [
        StartButtons(),
        StartLanguageButtons()
    ]
    handlers.extend(processing_handlers)

    for handler in handlers:
        if callback_query_data[0] == handler.prefix:
            await handler.callback(callback_query, callback_query_data)
            break


class StartButtons:
    def __init__(self):
        self.prefix = 'start_buttons'

    def menu_text(self, user):
        return tr.start_massage(user, user["name"])

    def keyboard(self, user):
        builder = InlineKeyboardBuilder()
        builder.button(text=tr.language(user), callback_data=f'{self.prefix}: language')
        builder.button(text='GitHub', callback_data=f'{self.prefix}: github')
        builder.adjust(2)
        return builder

    async def callback(self, callback_query: types.CallbackQuery, callback_query_data: list[str]):
        user, _ = utils.ensure_user_exists(callback_query)
        if callback_query_data[1] == 'language':
            await callback_query.message.edit_text(
                text=StartLanguageButtons().menu_text(user)
                , reply_markup=StartLanguageButtons().keyboard(user).as_markup()
            )
        elif callback_query_data[1] == 'github':
            await callback_query.bot.send_message(
                chat_id=callback_query.from_user.id,
                text='GitHub: https://github.com/A-l-e-s-t/clothing_bot'
            )

class StartLanguageButtons:
    def __init__(self):
        self.prefix = 'start_language_buttons'
    
    def menu_text(self, user):
        return tr.choose_language(user)

    def keyboard(self, user):
        builder = InlineKeyboardBuilder()
        builder.button(text=f'English', callback_data=f'{self.prefix}: en')
        builder.button(text=f'Українська', callback_data=f'{self.prefix}: ua')
        builder.button(text=tr.back(user), callback_data=f'{self.prefix}: back')
        builder.adjust(2, 1)
        return builder

    async def callback(self, callback_query: types.CallbackQuery, callback_query_data: list[str]):
        user, _ = utils.ensure_user_exists(callback_query)
        if callback_query_data[1] in languages.__args__:
            collection.members.mongo().update_one(
                {"user_id": user["user_id"]},
                {"$set": {"language": callback_query_data[1]}}
            )
            user, _ = utils.ensure_user_exists(callback_query)
            await callback_query.answer(tr.language_changed(user))
            await callback_query.message.edit_text(
                text=StartButtons().menu_text(user)
                , reply_markup=StartButtons().keyboard(user).as_markup()
            )
        elif callback_query_data[1] == 'back':
            await callback_query.message.edit_text(
                text=StartButtons().menu_text(user)
                , reply_markup=StartButtons().keyboard(user).as_markup()
            )


@start_router.message(CommandStart())
async def on_start_command(message: Message):
    user, _ = utils.ensure_user_exists(message)
    await message.answer(StartButtons().menu_text(user), reply_markup=StartButtons().keyboard(user).as_markup())

