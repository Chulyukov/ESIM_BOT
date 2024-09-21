import asyncio
import logging

from aiogram import Dispatcher
from aiohttp import web

from config import Config
from core import c_start, c_menu, c_get_my_esims, c_buy_esim, delete_esim
from robokassa_api import handle_payment

logging.basicConfig(level=logging.INFO)

bot = Config.BOT


async def main() -> None:
    dp = Dispatcher()

    dp.include_router(c_buy_esim.router)
    dp.include_router(c_get_my_esims.router)
    dp.include_router(c_menu.router)
    dp.include_router(delete_esim.router)
    dp.include_router(c_start.router)

    app = web.Application()
    app.router.add_post('/payment-result', handle_payment)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
