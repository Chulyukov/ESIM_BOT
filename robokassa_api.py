import hashlib

from aiogram import Router
from aiohttp import web

from config import Config
from db.users.db_payments import db_update_payment_status, db_get_chat_id_by_invoice_id

bot = Config.BOT
router = Router()


async def handle_result(request):
    data = await request.post()
    out_summ = data.get('OutSum')
    invoice_id = data.get('InvId')
    signature = data.get('SignatureValue')

    expected_signature = hashlib.md5(f"{out_summ}:{invoice_id}:{Config.TEST_PASSWORD2}".encode()).hexdigest()

    if signature.lower() == expected_signature.lower():
        # Платеж успешно обработан
        db_update_payment_status(invoice_id, 'paid')

        chat_id = db_get_chat_id_by_invoice_id(invoice_id)
        print(chat_id)
        if chat_id:
            await bot.send_message(chat_id, 'Ваш платеж успешно обработан!')
        return web.Response(text=f'OK{invoice_id}')
    else:
        return web.Response(text='bad sign')
