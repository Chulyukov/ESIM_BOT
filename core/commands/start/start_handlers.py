from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from core.commands.start.start_service import add_new_user_to_db, start_service
from core.helpful_methods import buy_esim_service
from db.db_start import db_check_user_exist

router = Router()


@router.message(CommandStart)
async def start_command(message: Message, state: FSMContext):
    """/start"""
    await state.clear()

    is_user_exist = db_check_user_exist(str(message.chat.id))
    if not is_user_exist:
        await add_new_user_to_db(message)
        await buy_esim_service(message)
    else:
        await start_service(message)
