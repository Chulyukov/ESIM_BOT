from mailbox import Message

from aiogram import Router
from aiogram.filters import Command

from core.commands.menu.menu_service import menu_service

router = Router()


@router.message(Command("menu"))
async def menu(message: Message):
    await menu_service(message)
