
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from core.commands.get_my_esims.get_my_esims_service import get_my_esims_service

router = Router()


@router.message(Command("get_my_esims"))
async def get_my_esims(message: Message):
    await get_my_esims_service(message)
