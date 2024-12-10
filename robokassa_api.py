import asyncio
import decimal
import hashlib
from urllib import parse

from bnesim_api import BnesimApi
from config import Config
from db.db_queries import (
    db_get_cli,
    db_get_all_data,
    db_get_chat_id_by_invoice_id,
    db_get_all_top_up_data,
    db_get_top_up_flag,
    db_get_username_by_invoice_id
)


def calculate_signature(*args) -> str:
    """
    Вычисляет MD5 подпись для набора аргументов.

    Args:
        *args: Аргументы для создания подписи.

    Returns:
        str: MD5 подпись.
    """
    return hashlib.md5(':'.join(str(arg) for arg in args).encode()).hexdigest()


def generate_payment_link(
        merchant_login: str,
        merchant_password_1: str,
        cost: decimal.Decimal,
        number: int,
        description: str,
        is_test: int = 0,
        robokassa_payment_url: str = 'https://auth.robokassa.ru/Merchant/Index.aspx'
) -> str:
    """
    Генерирует ссылку на оплату в системе Robokassa.

    Args:
        merchant_login (str): Логин мерчанта.
        merchant_password_1 (str): Пароль для подписи.
        cost (decimal.Decimal): Сумма оплаты.
        number (int): Номер заказа.
        description (str): Описание заказа.
        is_test (int): Флаг тестового режима (0 - реальный, 1 - тестовый).
        robokassa_payment_url (str): URL Robokassa.

    Returns:
        str: Ссылка на оплату.
    """
    signature = calculate_signature(merchant_login, cost, number, merchant_password_1)

    data = {
        'MerchantLogin': merchant_login,
        'OutSum': cost,
        'InvId': number,
        'Description': description,
        'SignatureValue': signature,
        'IsTest': is_test
    }
    return f'{robokassa_payment_url}?{parse.urlencode(data)}'


def handle_payment(data: dict):
    """
    Обрабатывает платеж и запускает соответствующую логику в зависимости от состояния.

    Args:
        data (dict): Данные платежа, включающие сумму, номер заказа и подпись.
    """
    out_summ = data.get('OutSum')
    invoice_id = data.get('InvId')
    signature = data.get('SignatureValue')

    # Проверяем корректность подписи
    expected_signature = calculate_signature(out_summ, invoice_id, Config.PASSWORD2)

    if signature.lower() != expected_signature.lower():
        raise ValueError("Подпись не совпадает, обработка платежа прервана.")

    # Получаем данные из базы
    chat_id = db_get_chat_id_by_invoice_id(invoice_id)
    bnesim = BnesimApi()
    cli = db_get_cli(chat_id)
    data_default = db_get_all_data(chat_id)
    top_up_data = db_get_all_top_up_data(chat_id)
    iccids_list = bnesim.get_iccids_of_user(cli)
    top_up_flag = db_get_top_up_flag(chat_id)
    username = db_get_username_by_invoice_id(invoice_id)

    # Выполняем действия в зависимости от наличия CLI
    if cli is None:
        cli = bnesim.activate_user(f"{username}_{chat_id}")
        handle_first_payment_order(cli, chat_id, data_default, bnesim)
    else:
        handle_payment_order(cli, bnesim, data_default, top_up_data, top_up_flag, chat_id, iccids_list)


from bnesim_api import BnesimApi
from config import Config
from db.db_queries import (
    db_update_cli,
    db_clean_data,
    db_clean_top_up_data,
    db_get_product_id
)
from aiogram.types import BufferedInputFile


async def handle_first_payment_order(cli, chat_id, data, bnesim):
    """
    Обрабатывает первый платеж и активирует eSIM.

    Args:
        cli (str): CLI пользователя.
        chat_id (str): ID чата.
        data (dict): Данные пользователя.
        bnesim (BnesimApi): Экземпляр API BNESIM.
    """
    product_id = db_get_product_id(data["country"], data["volume"])
    db_update_cli(chat_id, cli)
    active_esim = bnesim.activate_esim(cli, product_id)
    esim_info = bnesim.get_esim_info(active_esim["iccid"])

    while cli is None or active_esim["qr_code"] is None:
        await asyncio.sleep(1)

    db_clean_data(chat_id)

    await Config.BOT.send_photo(
        chat_id=chat_id,
        photo=BufferedInputFile(active_esim["qr_code"], "png_qr_code.png"),
        caption=(
            "*🎊 Поздравляем с приобретением вашей первой eSIM!*"
            f"\n\n📛 *Название вашей eSIM:* `{data['country'].title()} - {active_esim['iccid'][-4:]}`"
            f"\n🔗 *Ссылка для установки на iOS:* {esim_info['ios_link'].replace('_', '\\_')}"
            "\n\n📖 *Инструкции по установке:*"
            " [iPhone](https://telegra.ph/Kak-podklyuchit-eSIM-na-iPhone-07-27)"
            " | [Android](https://telegra.ph/Kak-podklyuchit-eSIM-na-Android-08-18)"
            " | [Samsung](https://telegra.ph/Kak-podklyuchit-eSIM-na-Samsung-08-18)"
            "\n\n🏝️ *Сложности? Обратитесь в службу заботы клиента eSIM Unity*"
        )
    )


async def handle_payment_order(cli, bnesim, data, top_up_data, top_up_flag, chat_id, iccids_list):
    """
    Обрабатывает продление или активацию eSIM.

    Args:
        cli (str): CLI пользователя.
        bnesim (BnesimApi): Экземпляр API BNESIM.
        data (dict): Данные пользователя.
        top_up_data (dict): Данные для пополнения.
        top_up_flag (bool): Флаг пополнения.
        chat_id (str): ID чата.
        iccids_list (list): Список ICCID.
    """
    if top_up_data and len(top_up_data) == 3 and top_up_data["iccid"] in iccids_list["iccids"] and top_up_flag:
        product_id = db_get_product_id(top_up_data["country"], top_up_data["volume"])
        api_response = bnesim.top_up_existing_esim(cli, top_up_data["iccid"], product_id)

        db_clean_top_up_data(chat_id)

        while api_response is None:
            await asyncio.sleep(1)

        await Config.BOT.send_message(
            chat_id=chat_id,
            text=(
                "*🎊 Успешное продление eSIM!*"
                f"\n\n📛 *Название вашей eSIM:* `{top_up_data['country'].title()} - {top_up_data['iccid'][-4:]}`"
                "\n\n🤖 *Используйте команду /get_my_esims для подробностей.*"
            )
        )
    else:
        product_id = db_get_product_id(data["country"], data["volume"])
        active_esim = bnesim.activate_esim(cli, product_id)
        esim_info = bnesim.get_esim_info(active_esim["iccid"])

        while active_esim["qr_code"] is None:
            await asyncio.sleep(1)

        db_clean_data(chat_id)

        await Config.BOT.send_photo(
            chat_id=chat_id,
            photo=BufferedInputFile(active_esim["qr_code"], "png_qr_code.png"),
            caption=(
                "*🎊 Спасибо за приобретение новой eSIM!*"
                f"\n\n📛 *Название вашей eSIM:* `{data['country'].title()} - {active_esim['iccid'][-4:]}`"
                f"\n🔗 *Ссылка для установки на iOS:* {esim_info['ios_link'].replace('_', '\\_')}"
                "\n\n📖 *Инструкции по установке:*"
                " [iPhone](https://telegra.ph/Kak-podklyuchit-eSIM-na-iPhone-07-27)"
                " | [Android](https://telegra.ph/Kak-podklyuchit-eSIM-na-Android-08-18)"
                " | [Samsung](https://telegra.ph/Kak-podklyuchit-eSIM-na-Samsung-08-18)"
                "\n\n🏝️ *Сложности? Обратитесь в службу заботы клиента eSIM Unity*"
            )
        )
