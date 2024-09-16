import asyncio
import logging

from aiogram import Dispatcher
from aiohttp import web

from config import Config
from core.commands import buy_esim, get_my_esims, donate, menu, start
from robokassa_api import handle_result

logging.basicConfig(level=logging.INFO)

bot = Config.BOT


async def main() -> None:
    dp = Dispatcher()

    dp.include_router(buy_esim.router)
    dp.include_router(get_my_esims.router)
    dp.include_router(donate.router)
    dp.include_router(menu.router)
    dp.include_router(start.router)

    app = web.Application()
    app.router.add_post('/payment-result', handle_result)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
