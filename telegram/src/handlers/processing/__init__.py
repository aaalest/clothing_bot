from aiogram import Router

from .process_image import process_image_router

processing_router = Router()

processing_router.include_routers(process_image_router)
