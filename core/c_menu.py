from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import Config

router = Router()

# Константы для текста меню
MENU_TEXT = (
    "*Основные действия бота*"
    "\n📖 /menu - главное меню"
    "\n🌐 /buy\_esim - приобрести eSIM"
    "\n🤝 /get\_my\_esims - посмотреть мои eSIM"
)

MENU_BUTTONS = [
    InlineKeyboardButton(text="📖 Список частых вопросов", url=Config.QUESTIONS_LINK),
    InlineKeyboardButton(text="🆘 Служба заботы клиента", url=Config.SUPPORT_LINK),
    InlineKeyboardButton(text="👥 Наш канал", url=Config.CHANNEL_LINK),
]


@router.message(Command("menu"))
async def menu(message: Message):
    kb = InlineKeyboardBuilder().add(*MENU_BUTTONS).adjust(1).as_markup()
    await message.answer(text=MENU_TEXT, reply_markup=kb)