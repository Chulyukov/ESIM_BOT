from datetime import datetime

from aiogram.types import Message

from core.helpful_methods import get_username
from db.db_start import db_add_user


async def add_new_user_to_db(message: Message):
    """Добавляем пользователя в БД при первичной активации"""
    username = get_username(message)
    db_add_user(str(message.chat.id), username, datetime.now())


async def start_service(message: Message):
    """Вторичный /start"""
    await message.answer("👋 *Добро пожаловать в нашего бота по работе с esim!*"
                         "\n\n📶 Этот бот занимается выдачей esim разных стран, чтобы у вас"
                         " была возможность выйти в Интернет из любой точки мира (список стран пока ограничен, но мы"
                         " активно работаем над его расширением 😉).\n\nНажмите /menu, чтобы посмотреть все доступные"
                         " команды бота.")

