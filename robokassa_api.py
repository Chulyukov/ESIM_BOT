import decimal
import hashlib
from urllib import parse

from aiohttp import web

from bnesim_api import BnesimApi
from config import Config
from core.commands.helpful_methods import add_new_user_after_payment, prolong_esim_after_payment, add_new_esim_after_payment
from db.users.db_cli import db_get_cli
from db.users.db_data import db_get_all_data
from db.users.db_payments import db_update_payment_status, db_get_chat_id_by_invoice_id, db_get_username_by_invoice_id
from db.users.db_top_up_data import db_get_all_top_up_data, db_get_top_up_flag


def calculate_signature(*args) -> str:
    return hashlib.md5(':'.join(str(arg) for arg in args).encode()).hexdigest()


def generate_payment_link(
        merchant_login: str,
        merchant_password_1: str,
        cost: decimal,
        number: int,
        description: str,
        is_test=0,
        robokassa_payment_url='https://auth.robokassa.ru/Merchant/Index.aspx',
) -> str:
    signature = calculate_signature(
        merchant_login,
        cost,
        number,
        merchant_password_1
    )

    data = {
        'MerchantLogin': merchant_login,
        'OutSum': cost,
        'InvId': number,
        'Description': description,
        'SignatureValue': signature,
        'IsTest': is_test
    }
    return f'{robokassa_payment_url}?{parse.urlencode(data)}'


async def handle_result(request):
    data = await request.post()
    out_summ = data.get('OutSum')
    invoice_id = data.get('InvId')
    signature = data.get('SignatureValue')

    expected_signature = hashlib.md5(f"{out_summ}:{invoice_id}:{Config.TEST_PASSWORD2}".encode()).hexdigest()

    chat_id = db_get_chat_id_by_invoice_id(invoice_id)
    if signature.lower() == expected_signature.lower():
        if out_summ in {111, 222, 333, 444}:
            await Config.BOT.send_message("🤗 Благодарим вас за поддержку нашего продукта!"
                                          "\n💪 Мы ежедневно прилагаем усилия, чтобы сделать его еще лучше.")
        else:
            bnesim = BnesimApi()
            cli = db_get_cli(chat_id)
            data = db_get_all_data(chat_id)
            top_up_data = db_get_all_top_up_data(chat_id)
            downloading_message = await Config.BOT.send_message(chat_id=chat_id,
                                                                text="*🚀 Подождите, обрабатываю данные платежа...*")
            iccids_list = bnesim.get_iccids_of_user(cli)
            top_up_flag = db_get_top_up_flag(chat_id)
            username = db_get_username_by_invoice_id(invoice_id)

            if cli is None:
                cli = bnesim.activate_user(f"{username}_{chat_id}")
                await add_new_user_after_payment(chat_id, data, cli, bnesim, downloading_message)
            elif (top_up_data is not None and len(top_up_data) == 3 and "iccid" in top_up_data
                  and top_up_data["iccid"] in [item for item in iccids_list["iccids"]]
                  and top_up_flag == 1):
                await prolong_esim_after_payment(chat_id, top_up_data, cli, bnesim, downloading_message)
            else:
                await add_new_esim_after_payment(chat_id, data, cli, bnesim, downloading_message)
        db_update_payment_status(invoice_id, 'paid')
        return web.Response(text=f'OK{invoice_id}')
    else:
        await Config.BOT.send_message(chat_id, 'произошла ошибка при обработке платежа! '
                                               'Деньги не были списаны, попробуйте заново.')
        db_update_payment_status(invoice_id, 'failed')
        await Config.BOT.send_message(chat_id=chat_id, text="Ваш платеж не прошел. Пожалуйста, попробуйте снова.")
        return web.Response(text='bad sign')
