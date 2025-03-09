from datetime import datetime

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import Config
from core.helpful_methods import get_username
from db.db_queries import db_check_user_exist, db_add_user

router = Router()

# Константы для текста меню
MENU_TEXT = (
    "*Основные действия бота*"
    "\n📖 /start - главное меню"
    "\n🌐 /buy\_esim - приобрести eSIM"
    # "\n🤝 /get\_my\_esims - посмотреть мои eSIM"
)

MENU_BUTTONS = [
    InlineKeyboardButton(text="📖 Список частых вопросов", url=Config.QUESTIONS_LINK),
    InlineKeyboardButton(text="🆘 Служба заботы клиента", url=Config.SUPPORT_LINK),
    InlineKeyboardButton(text="👥 Наш канал", url=Config.CHANNEL_LINK),
]


@router.message(CommandStart)
async def start_command(message: Message, state: FSMContext):
    await state.clear()

    chat_id = str(message.chat.id)
    is_user_exist = db_check_user_exist(chat_id)

    if not is_user_exist:
        username = get_username(message)
        db_add_user(chat_id, username, datetime.now())

    kb = InlineKeyboardBuilder().add(*MENU_BUTTONS).adjust(1).as_markup()
    await message.answer(text=MENU_TEXT, reply_markup=kb)
