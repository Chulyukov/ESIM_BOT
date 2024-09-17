
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import Config

router = Router()


@router.message(Command("menu"))
async def menu(message: Message):
    kb = InlineKeyboardBuilder().add(
        InlineKeyboardButton(text="📖 Список частых вопросов", url=Config.QUESTIONS_LINK),
        InlineKeyboardButton(text="🆘 Служба заботы клиента", url=Config.SUPPORT_LINK),
        InlineKeyboardButton(text="👥 Наш канал", url=Config.CHANNEL_LINK),
    ).adjust(1).as_markup()
    await message.answer(text="*Основные действия бота*"
                              "\n📖 /menu - главное меню"
                              "\n🌐 /buy\_esim - приобрести eSIM"
                              "\n🤝 /get\_my\_esims - посмотреть мои eSIM",
                         reply_markup=kb)
