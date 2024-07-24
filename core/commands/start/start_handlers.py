from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from core.commands.buy_esim.buy_esim_service import buy_esim_service
from core.commands.start.start_service import add_new_user_to_db, start_service
from db.db_start import db_check_user_exist

router = Router()


@router.message(CommandStart)
async def start_command(message: Message, state: FSMContext):
    """/start"""
    await state.clear()

    is_user_exist = db_check_user_exist(str(message.chat.id))
    if not is_user_exist:
        await add_new_user_to_db(message)

        # TODO: Написать метод после ответа CTO bnesim:
        #  "Получаем список продуктов - GET https://api.bnesim.com/v0.1/partners_pricing/?a=928G&format=json"
        await buy_esim_service(message)
    else:
        await start_service(message)
