import asyncio
import logging

from aiogram import Dispatcher

from config import Config
from core.commands import buy_esim, get_my_esims, donate, menu, start

logging.basicConfig(level=logging.INFO)

bot = Config.BOT


async def main() -> None:
    dp = Dispatcher()

    dp.include_router(buy_esim.router)
    dp.include_router(get_my_esims.router)
    dp.include_router(donate.router)
    dp.include_router(menu.router)
    dp.include_router(start.router)

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
