import decimal
import decimal
import hashlib
from urllib import parse

from bnesim_api import BnesimApi
from config import Config
from db.users.db_cli import db_get_cli
from db.users.db_data import db_get_all_data
from db.users.db_payments import db_get_chat_id_by_invoice_id, db_get_username_by_invoice_id
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


async def handle_payment(request):
    from core.helpful_methods import handle_payment_order, handle_first_payment_order

    data = await request.post()
    out_summ = data.get('OutSum')
    invoice_id = data.get('InvId')
    signature = data.get('SignatureValue')

    expected_signature = hashlib.md5(f"{out_summ}:{invoice_id}:{Config.PASSWORD2}".encode()).hexdigest()

    chat_id = db_get_chat_id_by_invoice_id(invoice_id)
    if signature.lower() == expected_signature.lower():
        bnesim = BnesimApi()
        cli = db_get_cli(chat_id)
        data = db_get_all_data(chat_id)
        top_up_data = db_get_all_top_up_data(chat_id)
        downloading_message = await Config.BOT.send_message(chat_id, "*🚀 Подождите, обрабатываю данные платежа...*")
        iccids_list = bnesim.get_iccids_of_user(cli)
        top_up_flag = db_get_top_up_flag(chat_id)
        username = db_get_username_by_invoice_id(invoice_id)
        if cli is None:
            cli = bnesim.activate_user(f"{username}_{chat_id}")
            await handle_first_payment_order(cli, chat_id, data, bnesim, downloading_message)
        else:
            await handle_payment_order(cli, bnesim, data, top_up_data,
                                       top_up_flag, chat_id, downloading_message, iccids_list)
