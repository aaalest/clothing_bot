from aiogram import types
import collection
import os


def ensure_user_exists(message: types.Message | types.InlineQuery | types.CallbackQuery) -> tuple[dict, bool]:
    user = collection.members.mongo().find_one({"user_id": message.from_user.id})
    existed = True
    if user is None:
        template = collection.members.Template(user_id=message.from_user.id, name=message.from_user.full_name)
        collection.members.mongo().insert_one(template.as_dict())
        user = collection.members.mongo().find_one({"user_id": message.from_user.id})
        existed = False
    return user, existed


def is_running_in_docker():
    return os.path.exists('/.dockerenv')