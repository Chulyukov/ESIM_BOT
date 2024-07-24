import asyncio
import logging

from aiogram import Dispatcher

from config import Config
from core.commands.buy_esim import buy_esim_handlers
from core.commands.get_my_esims import get_my_esims_handlers
from core.commands.menu import menu_handlers
from core.commands.start import start_handlers

logging.basicConfig(level=logging.INFO)

bot = Config.BOT


async def main() -> None:
    dp = Dispatcher()

    dp.include_router(buy_esim_handlers.router)
    dp.include_router(get_my_esims_handlers.router)
    dp.include_router(menu_handlers.router)
    dp.include_router(start_handlers.router)

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
