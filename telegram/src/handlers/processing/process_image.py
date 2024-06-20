import aiogram
from aiogram import Router, F
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types
from pydantic import BaseModel
from typing import Literal, List
from aiohttp import ClientResponseError
import asyncio
import threading

import api
import collection
import utils
from config import config
from translate import tr

process_image_router = Router()


class ProcessData(BaseModel):
    upper: Literal['jacket', 't-shirt', 'shirt', 'sweater', 'hoodie', 'coat', 'dress']
    upper_color: Literal['auto', 'black', 'white', 'red', 'green', 'blue', 'yellow', 'purple', 'orange', 'pink', 'brown', 'gray']
    lower: Literal['jeans', 'trousers', 'shorts', 'skirts']
    lower_color: Literal['auto', 'black', 'white', 'red', 'green', 'blue', 'yellow', 'purple', 'orange', 'pink', 'brown', 'gray']
    style: Literal['auto', 'casual', 'sport', 'formal', 'party']


@process_image_router.message(F.photo)
async def on_process_image_message(message: Message):
    backend = await api.get_suitable_backend()
    user, _ = utils.ensure_user_exists(message)
    if not backend:
        return await message.answer(tr.no_available_hosts(user), reply_markup=RetryGenerationButton().keyboard(user).as_markup())
    generations = collection.generations.mongo().find_one({"_id": user["generations"]})

    photo_id = chose_photo(message).file_id
    photo_file = await message.bot.get_file(photo_id)
    if generations:
        options = generations[-1]["options"]
    else:
        options = collection.generations.Template.Options(
            upper='jacket',
            upper_color='auto',
            lower='jeans',
            lower_color='auto',
            style='auto'
        )
    template = collection.generations.Template(
        user_id=message.from_user.id,
        input=collection.generations.Template.Input(
            file_id=photo_file.file_id,
            file_unique_id=photo_file.file_unique_id,
            file_size=photo_file.file_size,
            file_path=photo_file.file_path
        ),
        options=options
    )
    collection.generations.mongo().insert_one(template.as_dict())

    generation_document = collection.generations.mongo().find_one({"input.file_unique_id": photo_file.file_unique_id})
    if not generation_document:
        return await message.answer(tr.photo_not_found_upload_again(user))
    await message.reply(GenerationSettingsButtons().menu_text(user), reply_markup=GenerationSettingsButtons().keyboard(user, generation_document).as_markup())


class GenerationSettingsButtons:
    def __init__(self):
        self.prefix = 'generation_settings_buttons'

    def menu_text(self, user):
        return tr.choose_what_clothes_to_change_into(user)

    def keyboard(self, user, generation_document: dict):
        upper = generation_document["options"]["upper"]
        upper_color = generation_document["options"]["upper_color"]
        lower = generation_document["options"]["lower"]
        lower_color = generation_document["options"]["lower_color"]
        style = generation_document["options"]["style"]

        upper_types = {
            'jacket': tr.jacket(user),
            't-shirt': tr.tshirt(user),
            'shirt': tr.shirt(user),
            'sweater': tr.sweater(user),
            'hoodie': tr.hoodie(user),
            'coat': tr.coat(user),
            'dress': tr.dress(user)
        }
        upper_text = upper_types.get(upper, '')

        color_types = {
            'auto': tr.auto(user),
            'black': tr.black(user),
            'white': tr.white(user),
            'red': tr.red(user),
            'green': tr.green(user),
            'blue': tr.blue(user),
            'yellow': tr.yellow(user),
            'purple': tr.purple(user),
            'orange': tr.orange(user),
            'pink': tr.pink(user),
            'brown': tr.brown(user),
            'gray': tr.gray(user)
        }
        upper_color_text = color_types.get(upper_color, '')
        lower_color_text = color_types.get(lower_color, '')

        lower_types = {
            'jeans': tr.jeans(user),
            'trousers': tr.trousers(user),
            'shorts': tr.shorts(user),
            'skirts': tr.skirts(user)
        }
        lower_text = lower_types.get(lower, '')

        style_types = {
            'auto': tr.auto(user),
            'casual': tr.casual(user),
            'sport': tr.sport(user),
            'formal': tr.formal(user),
            'party': tr.party(user)
        }
        style_text = style_types.get(style, '')

        builder = InlineKeyboardBuilder()
        builder.button(text=f'{tr.upper(user)}: {upper_text}', callback_data=f'{self.prefix}: upper')
        builder.button(text=f'{tr.color(user)}: {upper_color_text}', callback_data=f'{self.prefix}: upper_color')

        builder.button(text=f'{tr.lower(user)}: {lower_text}', callback_data=f'{self.prefix}: lower')
        builder.button(text=f'{tr.color(user)}: {lower_color_text}', callback_data=f'{self.prefix}: lower_color')

        builder.button(text=f'{tr.style(user)}: {style_text}', callback_data=f'{self.prefix}: style')

        builder.button(text=f'{tr.generate(user)}', callback_data=f'{self.prefix}: generate')
        builder.adjust(2, 2, 1, 1)
        return builder

    async def callback(self, callback_query: types.CallbackQuery, callback_query_data: list[str | None]):
        user, _ = utils.ensure_user_exists(callback_query)
        replied_massage = callback_query.message.reply_to_message
        if not replied_massage:
            return await callback_query.answer(tr.message_not_found_try_again(user))

        if callback_query_data[1] == 'none':
            callback_query_data[1] = None

        generation_document = await find_generation_document(replied_massage)
        if not generation_document:
            return await callback_query.answer(tr.photo_not_found_upload_again(user))
        generation_document = collection.generations.mongo().find_one({"_id": generation_document["_id"]})

        if callback_query_data[1] == 'upper':
            await callback_query.message.edit_text(UpperSelectionButtons().menu_text(user), reply_markup=UpperSelectionButtons().keyboard(user).as_markup())
        elif callback_query_data[1] == 'upper_color':
            await callback_query.message.edit_text(UpperColorSelectionButtons().menu_text(user), reply_markup=UpperColorSelectionButtons().keyboard(user).as_markup())
        elif callback_query_data[1] == 'lower':
            await callback_query.message.edit_text(LowerSelectionButtons().menu_text(user), reply_markup=LowerSelectionButtons().keyboard(user).as_markup())
        elif callback_query_data[1] == 'lower_color':
            await callback_query.message.edit_text(LowerColorSelectionButtons().menu_text(user), reply_markup=LowerColorSelectionButtons().keyboard(user).as_markup())
        elif callback_query_data[1] == 'style':
            await callback_query.message.edit_text(StyleSelectionButtons().menu_text(user), reply_markup=StyleSelectionButtons().keyboard(user).as_markup())
        elif callback_query_data[1] == 'generate':
            await request_generation(replied_massage, callback_query.message)


class UpperSelectionButtons:
    def __init__(self):
        self.prefix = 'upper_selection_buttons'

    def menu_text(self, user):
        return tr.choose_upper_clothing(user)

    def keyboard(self, user):
        builder = InlineKeyboardBuilder()
        builder.button(text=tr.jacket(user), callback_data=f'{self.prefix}: jacket')
        builder.button(text=tr.tshirt(user), callback_data=f'{self.prefix}: t-shirt')
        builder.button(text=tr.shirt(user), callback_data=f'{self.prefix}: shirt')
        builder.button(text=tr.sweater(user), callback_data=f'{self.prefix}: sweater')
        builder.button(text=tr.hoodie(user), callback_data=f'{self.prefix}: hoodie')
        builder.button(text=tr.coat(user), callback_data=f'{self.prefix}: coat')
        builder.button(text=tr.dress(user), callback_data=f'{self.prefix}: dress')
        builder.button(text=f'{tr.back(user)} ⬅️', callback_data=f'{self.prefix}: cancel')
        builder.adjust(3, 3, 1, 1)
        return builder

    async def callback(self, callback_query: types.CallbackQuery, callback_query_data: list[str | None]):
        user, _ = utils.ensure_user_exists(callback_query)
        replied_massage = callback_query.message.reply_to_message
        if not replied_massage:
            return await callback_query.answer(tr.message_not_found_try_again(user))

        if callback_query_data[1] == 'none':
            callback_query_data[1] = None

        generation_document = await find_generation_document(replied_massage)
        if callback_query_data[1] in ProcessData.__annotations__["upper"].__args__:
            if not generation_document:
                return await callback_query.answer(tr.photo_not_found_upload_again(user))

            collection.generations.mongo().update_one(
                {"_id": generation_document["_id"]},
                {"$set": {"options.upper": callback_query_data[1]}}
            )
        generation_document = collection.generations.mongo().find_one({"_id": generation_document["_id"]})
        if not generation_document:
            return await callback_query.answer(tr.photo_not_found_upload_again(user))
        await callback_query.message.edit_text(GenerationSettingsButtons().menu_text(user),
                                               reply_markup=GenerationSettingsButtons().keyboard(user, generation_document).as_markup())

class UpperColorSelectionButtons:
    def __init__(self):
        self.prefix = 'upper_color_selection_buttons'

    def menu_text(self, user):
        return tr.choose_upper_color(user)

    def keyboard(self, user):
        builder = InlineKeyboardBuilder()
        builder.button(text=tr.auto(user), callback_data=f'{self.prefix}: auto')
        builder.button(text=tr.black(user), callback_data=f'{self.prefix}: black')
        builder.button(text=tr.white(user), callback_data=f'{self.prefix}: white')
        builder.button(text=tr.red(user), callback_data=f'{self.prefix}: red')

        builder.button(text=tr.green(user), callback_data=f'{self.prefix}: green')
        builder.button(text=tr.blue(user), callback_data=f'{self.prefix}: blue')
        builder.button(text=tr.yellow(user), callback_data=f'{self.prefix}: yellow')
        builder.button(text=tr.purple(user), callback_data=f'{self.prefix}: purple')

        builder.button(text=tr.orange(user), callback_data=f'{self.prefix}: orange')
        builder.button(text=tr.pink(user), callback_data=f'{self.prefix}: pink')
        builder.button(text=tr.brown(user), callback_data=f'{self.prefix}: brown')
        builder.button(text=tr.gray(user), callback_data=f'{self.prefix}: gray')
        builder.button(text=f'{tr.back(user)} ⬅️', callback_data=f'{self.prefix}: cancel')
        builder.adjust(4, 4, 4, 1)
        return builder

    async def callback(self, callback_query: types.CallbackQuery, callback_query_data: list[str | None]):
        user, _ = utils.ensure_user_exists(callback_query)
        replied_massage = callback_query.message.reply_to_message
        if not replied_massage:
            return await callback_query.answer(tr.message_not_found_try_again(user))

        if callback_query_data[1] == 'none':
            callback_query_data[1] = None

        generation_document = await find_generation_document(replied_massage)
        if callback_query_data[1] in ProcessData.__annotations__["upper_color"].__args__:
            if not generation_document:
                return await callback_query.answer(tr.photo_not_found_upload_again(user))

            collection.generations.mongo().update_one(
                {"_id": generation_document["_id"]},
                {"$set": {"options.upper_color": callback_query_data[1]}}
            )
        generation_document = collection.generations.mongo().find_one({"_id": generation_document["_id"]})
        if not generation_document:
            return await callback_query.answer(tr.photo_not_found_upload_again(user))
        await callback_query.message.edit_text(GenerationSettingsButtons().menu_text(user),
                                               reply_markup=GenerationSettingsButtons().keyboard(user, generation_document).as_markup())


class LowerSelectionButtons:
    def __init__(self):
        self.prefix = 'lower_selection_buttons'

    def menu_text(self, user):
        return tr.choose_lower_clothing(user)

    def keyboard(self, user):
        builder = InlineKeyboardBuilder()
        builder.button(text=tr.jeans(user), callback_data=f'{self.prefix}: jeans')
        builder.button(text=tr.trousers(user), callback_data=f'{self.prefix}: trousers')
        builder.button(text=tr.shorts(user), callback_data=f'{self.prefix}: shorts')
        builder.button(text=tr.skirts(user), callback_data=f'{self.prefix}: skirts')
        builder.button(text=f'{tr.back(user)} ⬅️', callback_data=f'{self.prefix}: cancel')
        builder.adjust(2, 2, 1)
        return builder

    async def callback(self, callback_query: types.CallbackQuery, callback_query_data: list[str | None]):
        user, _ = utils.ensure_user_exists(callback_query)
        replied_massage = callback_query.message.reply_to_message
        if not replied_massage:
            return await callback_query.answer(tr.message_not_found_try_again(user))

        if callback_query_data[1] == 'none':
            callback_query_data[1] = None

        generation_document = await find_generation_document(replied_massage)
        if callback_query_data[1] in ProcessData.__annotations__["lower"].__args__:
            if not generation_document:
                return await callback_query.answer(tr.photo_not_found_upload_again(user))

            collection.generations.mongo().update_one(
                {"_id": generation_document["_id"]},
                {"$set": {"options.lower": callback_query_data[1]}}
            )
        generation_document = collection.generations.mongo().find_one({"_id": generation_document["_id"]})
        if not generation_document:
            return await callback_query.answer(tr.photo_not_found_upload_again(user))
        await callback_query.message.edit_text(GenerationSettingsButtons().menu_text(user),
                                               reply_markup=GenerationSettingsButtons().keyboard(user, generation_document).as_markup())


class LowerColorSelectionButtons:
    def __init__(self):
        self.prefix = 'lower_color_selection_buttons'

    def menu_text(self, user):
        return tr.choose_lower_color(user)

    def keyboard(self, user):
        builder = InlineKeyboardBuilder()
        builder.button(text=tr.auto(user), callback_data=f'{self.prefix}: auto')
        builder.button(text=tr.black(user), callback_data=f'{self.prefix}: black')
        builder.button(text=tr.white(user), callback_data=f'{self.prefix}: white')
        builder.button(text=tr.red(user), callback_data=f'{self.prefix}: red')

        builder.button(text=tr.green(user), callback_data=f'{self.prefix}: green')
        builder.button(text=tr.blue(user), callback_data=f'{self.prefix}: blue')
        builder.button(text=tr.yellow(user), callback_data=f'{self.prefix}: yellow')
        builder.button(text=tr.purple(user), callback_data=f'{self.prefix}: purple')

        builder.button(text=tr.orange(user), callback_data=f'{self.prefix}: orange')
        builder.button(text=tr.pink(user), callback_data=f'{self.prefix}: pink')
        builder.button(text=tr.brown(user), callback_data=f'{self.prefix}: brown')
        builder.button(text=tr.gray(user), callback_data=f'{self.prefix}: gray')
        builder.button(text=f'{tr.back(user)} ⬅️', callback_data=f'{self.prefix}: cancel')
        builder.adjust(4, 4, 4, 1)
        return builder

    async def callback(self, callback_query: types.CallbackQuery, callback_query_data: list[str | None]):
        user, _ = utils.ensure_user_exists(callback_query)
        replied_massage = callback_query.message.reply_to_message
        if not replied_massage:
            return await callback_query.answer(tr.message_not_found_try_again(user))

        if callback_query_data[1] == 'none':
            callback_query_data[1] = None

        generation_document = await find_generation_document(replied_massage)
        if callback_query_data[1] in ProcessData.__annotations__["lower_color"].__args__:
            if not generation_document:
                return await callback_query.answer(tr.photo_not_found_upload_again(user))

            collection.generations.mongo().update_one(
                {"_id": generation_document["_id"]},
                {"$set": {"options.lower_color": callback_query_data[1]}}
            )
        generation_document = collection.generations.mongo().find_one({"_id": generation_document["_id"]})
        if not generation_document:
            return await callback_query.answer(tr.photo_not_found_upload_again(user))
        await callback_query.message.edit_text(GenerationSettingsButtons().menu_text(user),
                                               reply_markup=GenerationSettingsButtons().keyboard(user, generation_document).as_markup())


class StyleSelectionButtons:
    def __init__(self):
        self.prefix = 'style_selection_buttons'

    def menu_text(self, user):
        return tr.choose_style(user)

    def keyboard(self, user):
        builder = InlineKeyboardBuilder()
        builder.button(text=tr.auto(user), callback_data=f'{self.prefix}: auto')

        builder.button(text=tr.casual(user), callback_data=f'{self.prefix}: casual')
        builder.button(text=tr.sport(user), callback_data=f'{self.prefix}: sport')

        builder.button(text=tr.formal(user), callback_data=f'{self.prefix}: formal')
        builder.button(text=tr.party(user), callback_data=f'{self.prefix}: party')

        builder.button(text=f'{tr.back(user)} ⬅️', callback_data=f'{self.prefix}: cancel')
        builder.adjust(1, 2, 2, 1)
        return builder

    async def callback(self, callback_query: types.CallbackQuery, callback_query_data: list[str | None]):
        user, _ = utils.ensure_user_exists(callback_query)
        replied_massage = callback_query.message.reply_to_message
        if not replied_massage:
            return await callback_query.answer(tr.message_not_found_try_again(user))

        if callback_query_data[1] == 'none':
            callback_query_data[1] = None

        generation_document = await find_generation_document(replied_massage)
        if callback_query_data[1] in ProcessData.__annotations__["style"].__args__:
            if not generation_document:
                return await callback_query.answer(tr.photo_not_found_upload_again(user))

            collection.generations.mongo().update_one(
                {"_id": generation_document["_id"]},
                {"$set": {"options.style": callback_query_data[1]}}
            )
        generation_document = collection.generations.mongo().find_one({"_id": generation_document["_id"]})
        if not generation_document:
            return await callback_query.answer(tr.photo_not_found_upload_again(user))
        await callback_query.message.edit_text(GenerationSettingsButtons().menu_text(user),
                                               reply_markup=GenerationSettingsButtons().keyboard(user, generation_document).as_markup())


class GeneratedPhotoButtons:
    def __init__(self):
        self.prefix = 'generated_photo_buttons'

    def keyboard(self, user):
        builder = InlineKeyboardBuilder()
        builder.button(text=f'{tr.regenerate(user)}', callback_data=f'{self.prefix}: regenerate')
        builder.button(text=f'{tr.modify_generation(user)}', callback_data=f'{self.prefix}: modify_generation')
        builder.adjust(3, 1)
        return builder

    async def callback(self, callback_query: types.CallbackQuery, callback_query_data: list[str | None]):
        user, _ = utils.ensure_user_exists(callback_query)
        replied_massage = callback_query.message.reply_to_message
        if not replied_massage:
            return await callback_query.answer(tr.message_not_found_try_again(user))

        if callback_query_data[1] == 'none':
            callback_query_data[1] = None

        generation_document = await find_generation_document(replied_massage)
        if not generation_document:
            return await callback_query.answer(tr.photo_not_found_upload_again(user))

        if callback_query_data[1] == 'regenerate':
            await request_generation(replied_massage)
        elif callback_query_data[1] == 'modify_generation':
            await replied_massage.reply(GenerationSettingsButtons().menu_text(user),
                                        reply_markup=GenerationSettingsButtons().keyboard(user, generation_document).as_markup())


class GeneratingProgressButtons:
    def __init__(self):
        self.prefix = 'generating_progress_buttons'

    def keyboard(self, user):
        builder = InlineKeyboardBuilder()
        builder.button(text=f'{tr.cancel(user)}', callback_data=f'{self.prefix}: cancel')
        builder.button(text=f'{tr.modify_generation(user)}', callback_data=f'{self.prefix}: modify_generation')
        builder.adjust(2, 1)
        return builder

    async def callback(self, callback_query: types.CallbackQuery, callback_query_data: list[str]):
        user, _ = utils.ensure_user_exists(callback_query)
        replied_massage = callback_query.message.reply_to_message
        if not replied_massage:
            return await callback_query.answer(tr.message_not_found_try_again(user))

        generation_document = await find_generation_document(replied_massage)
        if not generation_document:
            return await callback_query.answer(tr.photo_not_found_upload_again(user))

        if callback_query_data[1] == 'cancel':
            await replied_massage.reply('Feature is in development')
        elif callback_query_data[1] == 'modify_generation':
            await replied_massage.reply(GenerationSettingsButtons().menu_text(user),
                                        reply_markup=GenerationSettingsButtons().keyboard(user, generation_document).as_markup())

class RetryGenerationButton:
    def __init__(self):
        self.prefix = 'retry_generation_button'

    def keyboard(self, user):
        builder = InlineKeyboardBuilder()
        builder.button(text=f'{tr.regenerate(user)}', callback_data=f'{self.prefix}: regenerate')
        return builder

    async def callback(self, callback_query: types.CallbackQuery, callback_query_data: list[str]):
        user, _ = utils.ensure_user_exists(callback_query)
        replied_massage = callback_query.message.reply_to_message
        if not replied_massage:
            return await callback_query.answer(tr.message_not_found_try_again(user))

        generation_document = await find_generation_document(replied_massage)
        if not generation_document:
            return await callback_query.answer(tr.photo_not_found_upload_again(user))

        if callback_query_data[1] == 'regenerate':
            await callback_query.bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
            await request_generation(replied_massage)



def chose_photo(message: Message, max_size=1_000_000):
    chosen_photo = message.photo[-1]
    # for photo in message.photo:
    #     if photo.width > chosen_photo.width and photo.file_size < max_size:
    #         chosen_photo = photo
    return chosen_photo


async def find_generation_document(message: Message):
    last_photo = message.photo.copy()[-1]
    print(f'last_photo: {last_photo}')
    # photo_file = await message.bot.get_file(last_photo.file_id)
    # print(f'find_generation_document: file_path: {photo_file.file_path}')
    print(f'find_generation_document: file_unique_id: {last_photo.file_unique_id}')
    generation_document = collection.generations.mongo().find_one({"input.file_unique_id": last_photo.file_unique_id})
    if generation_document:
        return generation_document
    return None


async def request_generation(message: Message, answer_message: Message = None):
    user, _ = utils.ensure_user_exists(message)
    generation_document = await find_generation_document(message)
    if not generation_document:
        return await message.answer(tr.photo_not_found_upload_again(user))

    backend = await api.get_suitable_backend()
    if not backend:
        return await message.answer(tr.no_available_hosts(user), reply_markup=RetryGenerationButton().keyboard(user).as_markup())
    # else:
    #     message_answer = await message.answer(f'Processing the image on {backend}')  # TODO: Queue size

    await GenerationQueue.add(message, answer_message, generation_document)
    print('Generation request has been sent')


async def request_generation_in_thread(message, answer_message, backend, generation_document):
    user = collection.members.mongo().find_one({"user_id": message.from_user.id})
    file_path = generation_document["input"]["file_path"]
    user_id = message.from_user.id
    bot = aiogram.Bot(token=config.bot.token)
    if answer_message:
        await bot.edit_message_text(chat_id=user_id, message_id=answer_message.message_id, text=f'{tr.generating(user)} ⏳',
                                    reply_markup=GeneratingProgressButtons().keyboard(user).as_markup())
    else:
        answer_message = await bot.send_message(user_id, f'{tr.generating(user)} ⏳', reply_to_message_id=message.message_id,
                                                reply_markup=GeneratingProgressButtons().keyboard(user).as_markup())

    # try:
    response = await api.generate(file_path, bot, backend, generation_document)
    # except Exception as e:
    #     if isinstance(e, ClientResponseError):
    #         # Handle ClientResponseError
    #         if e.message == 'Not Found' and e.status == 404:
    #             await bot.edit_message_text(tr.photo_not_found_upload_again(user), user_id, message_id=answer_message.message_id)
    #     else:
    #         # Handle other exceptions
    #         print('Error:', e)
    #         await bot.edit_message_text(tr.an_error_occurred_during_image_processing(user), user_id,
    #                                     message_id=answer_message.message_id, reply_markup=RetryGenerationButton().keyboard(user).as_markup())
    #     return

    if 'image' in response:
        collection.members.mongo().update_one(
            {"_id": user["_id"]},
            {"$set": {"generations": user["generations"] + [generation_document["_id"]]}}
        )
        await bot.delete_message(user_id, answer_message.message_id)
        await bot.send_photo(user_id, response["image"],
                             reply_markup=GeneratedPhotoButtons().keyboard(user).as_markup(), reply_to_message_id=message.message_id)

        # await bot.edit_message_media(chat_id=user_id, message_id=answer_message.message_id, media=types.InputMediaPhoto(media=response["image"]))
    elif response["message"] == 'clothing not found':
        await bot.edit_message_text(tr.clothing_was_not_found_please_try_a_different_photo(user), user_id,
                                    message_id=answer_message.message_id)
    else:
        await bot.edit_message_text(tr.an_error_occurred_during_image_processing(user), user_id,
                                    message_id=answer_message.message_id, reply_markup=RetryGenerationButton().keyboard(user).as_markup())


class generation_queue:
    def __init__(self):
        self.queue = []
        self._run_in_new_thread(self._process())

    async def add(self, message: Message, answer_message: Message, generation_document: dict):
        self.queue.append({
            "message": message,
            "answer_message": answer_message,
            "generation_document": generation_document
        })

    async def _process(self):
        import time
        while True:
            while len(self.queue) > 0:
                # TODO: Request generation only when the is a free suitable backend
                now = time.time()
                self._run_in_new_thread(request_generation_in_thread(
                    self.queue[0]["message"],
                    self.queue[0]["answer_message"],
                    await api.get_suitable_backend(),  # TODO: Temporary solution
                    self.queue[0]["generation_document"]
                ))
                print(f'Generation request has been sent in {time.time() - now} seconds')
                self.queue.pop(0)
            await asyncio.sleep(0.1)

            # bot = aiogram.Bot(token=config.bot.token)
            # await bot.send_message(1285205193, 'adeo[pirfhgpiahebrnsdl;vnbapeoriuhgpeo;')
            # await asyncio.sleep(1)

    def _run_in_new_thread(self, coroutine):
        def thread_func():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(coroutine)
            loop.close()

        thread = threading.Thread(target=thread_func)
        thread.start()


GenerationQueue = generation_queue()

handlers = [
    GenerationSettingsButtons(),
    UpperSelectionButtons(),
    UpperColorSelectionButtons(),
    LowerSelectionButtons(),
    LowerColorSelectionButtons(),
    StyleSelectionButtons(),
    GeneratedPhotoButtons(),
    RetryGenerationButton()
]
