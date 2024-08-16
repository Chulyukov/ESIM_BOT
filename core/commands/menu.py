
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import Config

router = Router()


@router.message(Command("menu"))
async def menu(message: Message):
    await message.answer(text="*Основные действия бота*"
                              "\n📖 /menu - главное меню"
                              "\n🌐 /buy\_esim - приобрести esim"
                              "\n🤝 /get\_my\_esims - посмотреть мои esim"
                              "\n🎗️ /donate - Поддержать проект"
                              f"\n\n📖 *Список популярных вопросов:* {Config.QUESTIONS_LINK}"
                              f"\n\n🆘 *Обратиться в службу заботы клиента:* {Config.SUPPORT_LINK}"
                              f"\n\n👥 *Наш канал:* {Config.CHANNEL_LINK}", disable_web_page_preview=True)
