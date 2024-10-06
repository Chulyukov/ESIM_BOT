from datetime import datetime

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from core.helpful_methods import choose_country, get_username, choose_direction
from db.db_start import db_check_user_exist, db_add_user

router = Router()


@router.message(CommandStart)
async def start_command(message: Message, state: FSMContext):
    """/start"""
    await state.clear()

    is_user_exist = db_check_user_exist(str(message.chat.id))
    if is_user_exist:
        await message.answer("👋 *Добро пожаловать в нашего бота по работе с eSIM!*"
                             "\n\n📶 Этот бот занимается выдачей eSIM разных стран, чтобы у вас была возможность выйти в Интернет из любой точки мира."
                             "🌍 *Доступно более 170 направлений!"
                             "\n\n👉Нажмите /buy\_esim, чтобы запустить процедуру покупки eSIM,"
                             " а все доступные команды бота доступны по команде /menu!")
    else:
        db_add_user(str(message.chat.id), get_username(message), datetime.now())
        await choose_direction(message)
