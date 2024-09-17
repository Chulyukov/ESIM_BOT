import asyncio
import decimal
import hashlib
from urllib import parse

from aiogram.types import BufferedInputFile
from aiohttp import web

from bnesim_api import BnesimApi
from config import Config
from db.db_bnesim_products import db_get_product_id
from db.users.db_cli import db_get_cli, db_update_cli
from db.users.db_data import db_get_all_data, db_clean_data
from db.users.db_payments import db_update_payment_status, db_get_chat_id_by_invoice_id, db_get_username_by_invoice_id
from db.users.db_top_up_data import db_get_all_top_up_data, db_get_top_up_flag, db_clean_top_up_data


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

    expected_signature = hashlib.md5(f"{out_summ}:{invoice_id}:{Config.PASSWORD2}".encode()).hexdigest()

    chat_id = db_get_chat_id_by_invoice_id(invoice_id)
    if signature.lower() == expected_signature.lower():
        if out_summ in {111, 222, 333, 444}:
            await Config.BOT.send_message(chat_id=chat_id, text="🤗 Благодарим вас за поддержку нашего продукта!"
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
                product_id = db_get_product_id(data[0], data[1])
                db_update_cli(chat_id, cli)
                active_esim = bnesim.activate_esim(cli, product_id)
                while cli is None and active_esim[1] is None:
                    await asyncio.sleep(1)
                db_clean_data(chat_id)
                await Config.BOT.delete_message(chat_id=chat_id, message_id=downloading_message.message_id)
                await Config.BOT.send_photo(chat_id=chat_id, photo=BufferedInputFile(active_esim[1],
                                                                                     "png_qr_code.png"),
                                            caption="*🎊 Поздравляем с приобретением вашей первой eSIM!*"
                                                    "\n\n☎️ *Название вашей eSIM:*"
                                                    f" `{data[0].capitalize()} - {active_esim[0][-4:]}`"
                                                    "\n\n*📖 Инструкция по установке:*"
                                                    " [iPhone](https://telegra.ph/Kak-podklyuchit-eSIM-na-iPhone-07-27)"
                                                    " | [Android](https://telegra.ph/Kak-podklyuchit-eSIM-na-Android-08-18)"
                                                    " | [Samsung](https://telegra.ph/Kak-podklyuchit-eSIM-na-Samsung-08-18)"
                                                    " | [Huawei](https://telegra.ph/Kak-podklyuchit-eSIM-na-Huawei-08-18)"
                                                    " | [Google Pixel](https://telegra.ph/Kak-podklyuchit-eSIM-na-Pixel-08-24)"
                                                    "\n\n🏝️ Если во время установки у вас возникли какие-либо сложности,"
                                                    f" обратитесь в службу заботы клиента eSIM Unity: {Config.SUPPORT_SIMPLE_LINK}"
                                                    "\n\n🤖 Также вы можете посмотреть подробную информацию о ваших eSIM"
                                                    " с помощью команды /get\_my\_esims или перейти в главное меню "
                                                    "/menu")
            elif (top_up_data is not None and len(top_up_data) == 3 and "iccid" in top_up_data
                  and top_up_data["iccid"] in [item for item in iccids_list["iccids"]]
                  and top_up_flag == 1):
                product_id = db_get_product_id(top_up_data["country"], top_up_data["volume"])
                iccids_map = bnesim.get_iccids_of_user(cli)
                if top_up_data["iccid"] in iccids_map["iccids"]:
                    api_answer = bnesim.top_up_existing_esim(cli, top_up_data["iccid"], product_id)
                    db_clean_top_up_data(chat_id)
                    while api_answer is None:
                        await asyncio.sleep(1)
                    await Config.BOT.delete_message(chat_id=chat_id, message_id=downloading_message.message_id)
                    await Config.BOT.send_message(chat_id=chat_id, text="*🎊 Успешное продление eSIM!*"
                                                  f"\n\n*📛 Название вашей eSIM:*"
                                                  f" `{top_up_data["country"].capitalize()} - {top_up_data["iccid"][-4:]}`"
                                                  f"\n\n🤖 Вы можете посмотреть инструкцию по установке и"
                                                  f" подробную информацию о ваших eSIM с помощью команды /get\_my\_esims")
            else:
                product_id = db_get_product_id(data[0], data[1])
                active_esim = bnesim.activate_esim(cli, product_id)
                while active_esim[1] is None:
                    await asyncio.sleep(1)
                db_clean_data(chat_id)
                await Config.BOT.delete_message(chat_id=chat_id, message_id=downloading_message.message_id)
                await Config.BOT.send_photo(chat_id=chat_id, photo=BufferedInputFile(active_esim[1],
                                                                                     "png_qr_code.png"),
                                            caption="🎊 Спасибо за приобретение новой eSIM!"
                                                    "\n\n📛 *Название вашей eSIM:*"
                                                    f" `{data[0].capitalize()} - {active_esim[0][-4:]}`"
                                                    "\n\n*Инструкция по установке:*"
                                                    " [iPhone](https://telegra.ph/Kak-podklyuchit-eSIM-na-iPhone-07-27)"
                                                    " | [Android](https://telegra.ph/Kak-podklyuchit-eSIM-na-Android-08-18)"
                                                    " | [Samsung](https://telegra.ph/Kak-podklyuchit-eSIM-na-Samsung-08-18)"
                                                    " | [Huawei](https://telegra.ph/Kak-podklyuchit-eSIM-na-Huawei-08-18)"
                                                    " | [Google Pixel](https://telegra.ph/Kak-podklyuchit-eSIM-na-Pixel-08-24)"
                                                    "\n\n🏝️ Если во время установки у вас возникли какие-либо сложности,"
                                                    f" обратитесь в службу заботы клиента eSIM Unity: {Config.SUPPORT_SIMPLE_LINK}"
                                                    "\n\n🤖 Также вы можете посмотреть подробную информацию о ваших eSIM"
                                                    " с помощью команды /get\_my\_esims или перейти в главное меню "
                                                    "/menu")
        db_update_payment_status(invoice_id, 'paid')
        return web.Response(text=f'OK{invoice_id}')
    else:
        await Config.BOT.send_message(chat_id=chat_id, text="Ваш платеж не прошел. Пожалуйста, попробуйте снова.")
        db_update_payment_status(invoice_id, 'failed')
        return web.Response(text='bad sign')
