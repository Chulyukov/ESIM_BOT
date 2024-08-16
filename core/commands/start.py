from datetime import datetime

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from core.helpful_methods import buy_esim_service, get_username
from db.db_start import db_check_user_exist, db_add_user

router = Router()


@router.message(CommandStart)
async def start_command(message: Message, state: FSMContext):
    """/start"""
    await state.clear()

    is_user_exist = db_check_user_exist(str(message.chat.id))
    if not is_user_exist:
        username = get_username(message)
        db_add_user(str(message.chat.id), username, datetime.now())
        await buy_esim_service(message)
    else:
        await message.answer("👋 *Добро пожаловать в нашего бота по работе с esim!*"
                             "\n\n📶 Этот бот занимается выдачей esim разных стран, чтобы у вас"
                             " была возможность выйти в Интернет из любой точки мира (список стран пока ограничен, но мы"
                             " активно работаем над его расширением 😉).\n\nНажмите /menu, чтобы посмотреть все доступные"
                             " команды бота.")
