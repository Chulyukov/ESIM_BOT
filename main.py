import asyncio
import logging

from aiogram import Dispatcher

from config import Config
from core import c_start, c_menu, c_get_my_esims, c_buy_esim, delete_esim

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    dp = Dispatcher()

    dp.include_router(c_buy_esim.router)
    dp.include_router(c_get_my_esims.router)
    dp.include_router(c_menu.router)
    dp.include_router(delete_esim.router)
    dp.include_router(c_start.router)

    await dp.start_polling(Config.BOT)


if __name__ == '__main__':
    asyncio.run(main())
