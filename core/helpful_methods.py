import asyncio
import random

from aiogram import types
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import Config
from db.countries.db_pay_pic_link import db_get_pay_pic_link
from db.db_bnesim_products import db_get_price_data, db_get_product_id
from db.users.db_cli import db_update_cli
from db.users.db_data import db_get_data_country, db_update_data_volume, db_clean_data
from db.users.db_payments import db_save_invoice_user
from db.users.db_top_up_data import db_get_top_up_data_country, db_update_top_up_data_volume, \
    db_update_top_up_flag_true, db_update_top_up_flag_false, db_clean_top_up_data
from robokassa_api import generate_payment_link


def get_username(message):
    if message.from_user.username is None:
        username = message.from_user.first_name
    else:
        username = '@' + message.from_user.username
    return username


async def choose_country(msg: Message | CallbackQuery):
    buttons = [
        InlineKeyboardButton(text="🇹🇷Турция", callback_data="choose_payment_method_turkey"),
        InlineKeyboardButton(text="🇹🇭Тайланд", callback_data="choose_payment_method_thailand"),
        InlineKeyboardButton(text="🇬🇪Грузия", callback_data="choose_payment_method_georgia"),
        InlineKeyboardButton(text="🇪🇬Египет", callback_data="choose_payment_method_egypt"),
        InlineKeyboardButton(text="🇮🇹Италия", callback_data="choose_payment_method_italy"),
        InlineKeyboardButton(text="🇪🇺Европа", callback_data="choose_payment_method_europe"),
    ]
    kb = build_keyboard(buttons, (2,))

    message_text = (
        "🚨 *Перед тем, как выбрать страну,"
        " обязательно удостоверьтесь в том, что ваш смартфон поддерживает технологию eSIM*."
        "\nВы можете проверить это, следуя шагам из"
        " [инструкции](https://telegra.ph/Kak-ponyat-chto-u-menya-est-vozmozhnost-podklyuchit-eSIM-07-27)."
        "\n\n👇*Выберите одну из доступных стран (список стран со временем будет активно пополняться).*"
    )
    if isinstance(msg, CallbackQuery):
        await msg.message.edit_text(text=message_text, reply_markup=kb, disable_web_page_preview=True)
    else:
        await msg.answer(text=message_text, reply_markup=kb, disable_web_page_preview=True)


def build_keyboard(buttons, adjust_params):
    kb = InlineKeyboardBuilder()
    for button in buttons:
        kb.add(button)
    return kb.adjust(*adjust_params).as_markup()


def get_plan_prices(currency, chat_id, is_top_up=False):
    # Определяем страну в зависимости от флага is_top_up
    country = db_get_top_up_data_country(chat_id) if is_top_up else db_get_data_country(chat_id)

    # Получаем данные о ценах
    price_data = db_get_price_data(country)

    # Определяем множитель в зависимости от валюты
    multiplier = (
        Config.EURO_EXCHANGE_RATE if currency == 'RUB'
        else Config.EURO_EXCHANGE_RATE / 1.5
    )

    # Рассчитываем цены для каждого плана
    prices = {}
    for plan in [3, 5, 10, 20]:
        price = float(price_data[plan]["price"])
        prices[plan] = int(price * multiplier * 1.04 * Config.PERCENT_OF_STONX)

    return prices


async def prepare_payment_order(callback: CallbackQuery, currency, is_top_up=False):
    chat_id = callback.message.chat.id
    gb_amount = int(callback.data.split("_")[-1])
    if is_top_up:
        db_update_top_up_flag_true(chat_id)
        country = db_get_top_up_data_country(chat_id)
        db_update_top_up_data_volume(chat_id, gb_amount)
    else:
        db_update_top_up_flag_false(chat_id)
        country = db_get_data_country(chat_id)
        db_update_data_volume(chat_id, gb_amount)
    prices = get_plan_prices(currency, chat_id, is_top_up)
    amount = prices[gb_amount]
    photo_url = db_get_pay_pic_link(country)
    if currency == "XTR":
        invoice_params = {
            'chat_id': callback.from_user.id,
            'title': f"Счет “{country.capitalize()} - {gb_amount}GB”",
            'description': f"Вы выбрали тариф “{country.capitalize()} - {gb_amount}”."
                           " ⚠️ Учтите: активным для оплаты считается счет, выставленный последним в диалоге.",
            'provider_token': Config.YOKASSA_TEST_TOKEN if currency == 'RUB' else '',
            'currency': 'rub' if currency == 'RUB' else 'XTR',
            'photo_url': photo_url if photo_url else '',
            'photo_width': 485,
            'photo_height': 300,
            'is_flexible': False,
            'prices': [types.LabeledPrice(label=f"eSIM payment using {currency}",
                                          amount=amount * 100 if currency == 'RUB' else amount)],
            'payload': "test-invoice-payload"
        }
        await Config.BOT.send_invoice(**invoice_params)
    else:
        digits = random.randint(3, 10)
        invoice_id = random.randint(10 ** (digits - 1), (10 ** digits) - 1)
        db_save_invoice_user(invoice_id, chat_id, get_username(callback.message))
        payment_link = generate_payment_link(Config.MERCHANT_LOGIN, Config.PASSWORD1, amount, invoice_id,
                                             f"{country} - {amount}", 0)
        kb = InlineKeyboardBuilder().add(
            InlineKeyboardButton(text="💳 Оплатить", url=payment_link)
        ).as_markup()
        if photo_url:
            await Config.BOT.send_photo(chat_id=chat_id,
                                        photo=photo_url,
                                        caption=f"Вы выбрали тариф"
                                                f" “{country.capitalize()} - {gb_amount}”."
                                                f"\n\n⚠️ Учтите: активным для оплаты считается счет,"
                                                f" выставленный последним в диалоге.",
                                        reply_markup=kb)
        else:
            await Config.BOT.send_message(chat_id=chat_id, text=f"Вы выбрали тариф"
                                                                f" “{country.capitalize()} - {gb_amount}”."
                                                                f"\n\n⚠️ Учтите: активным для оплаты считается счет,"
                                                                f" выставленный последним в диалоге.", reply_markup=kb)


async def handle_first_payment_order(cli, chat_id, data, bnesim, downloading_message):
    product_id = db_get_product_id(data[0], data[1])
    db_update_cli(chat_id, cli)
    active_esim = bnesim.activate_esim(cli, product_id)
    esim_info = bnesim.get_esim_info(active_esim["iccid"])
    while cli is None and active_esim["qr_code"] is None:
        await asyncio.sleep(1)
    db_clean_data(chat_id)
    await Config.BOT.delete_message(chat_id=chat_id, message_id=downloading_message.message_id)
    await Config.BOT.send_photo(chat_id=chat_id, photo=BufferedInputFile(active_esim["qr_code"],
                                                                         "png_qr_code.png"),
                                caption="*🎊 Поздравляем с приобретением вашей первой eSIM!*"
                                        "\n\n☎️ *Название вашей eSIM:*"
                                        f" `{data[0].capitalize()} - {active_esim['iccid'][-4:]}`"
                                        f"\n*🔗 Ссылка для прямой установки на IOS:* {esim_info['ios_link'].replace("_", "\_")}"
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


async def handle_payment_order(cli, bnesim, data, top_up_data, top_up_flag,
                               chat_id, downloading_message, iccids_list):
    if (top_up_data is not None and len(top_up_data) == 3 and "iccid" in top_up_data
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
        esim_info = bnesim.get_esim_info(active_esim["iccid"])
        while active_esim["qr_code"] is None:
            await asyncio.sleep(1)
        db_clean_data(chat_id)
        await Config.BOT.delete_message(chat_id=chat_id, message_id=downloading_message.message_id)
        await Config.BOT.send_photo(chat_id=chat_id, photo=BufferedInputFile(active_esim["qr_code"],
                                                                             "png_qr_code.png"),
                                    caption="🎊 Спасибо за приобретение новой eSIM!"
                                            "\n\n📛 *Название вашей eSIM:*"
                                            f" `{data[0].capitalize()} - {active_esim['iccid'][-4:]}`"
                                            f"\n*🔗 Ссылка для прямой установки на IOS:* {esim_info['ios_link'].replace("_", "\_")}"
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
