import asyncio
import random
from datetime import datetime

from aiogram import types
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import Config
from db.countries.db_pay_pic_link import db_get_pay_pic_link
from db.db_bnesim_products import db_get_price_data, db_get_product_id
from db.db_buy_esim import db_get_emoji_from_two_tables, db_get_ru_name_from_two_tables
from db.users.db_cli import db_update_cli
from db.users.db_data import db_get_data_country, db_update_data_volume, db_clean_data, db_get_all_data
from db.users.db_payments import db_save_invoice_user
from db.users.db_top_up_data import db_get_top_up_data_country, db_update_top_up_data_volume, \
    db_update_top_up_flag_true, db_update_top_up_flag_false, db_clean_top_up_data
from db.users.db_username import db_get_username
from get_euro_rate import get_euro_to_rub_rate
from robokassa_api import generate_payment_link


def get_username(message):
    if message.from_user.username is None:
        username = message.from_user.first_name
    else:
        username = '@' + message.from_user.username
    return username


async def choose_direction(msg: Message | CallbackQuery):
    message_text = ("🚨 *Перед тем, как выбрать направление,"
                    " обязательно удостоверьтесь в том, что ваш смартфон поддерживает технологию eSIM*."
                    "\nВы можете проверить это, следуя шагам из"
                    " [инструкции](https://telegra.ph/Kak-ponyat-chto-u-menya-est-vozmozhnost-podklyuchit-eSIM-07-27)."
                    "\n\n🔍 Вы можете в любое время *ввести название страны* на русском или английском языке, и *бот покажет все подходящие варианты.* Просто напишите название, и вы получите список стран, соответствующих вашему запросу!"
                    "\n\n🆘 Если у вас возникли какие-либо сложности, пожалуйста, свяжитесь со [службой заботы клиента](https://t.me/esim_unity_support)."
                    "\n\n👇*Выберите раздел.*")
    kb = build_keyboard([
        InlineKeyboardButton(text="🔥 Популярные направления", callback_data="popular_directions"),
        InlineKeyboardButton(text="📍 Отдельные страны", callback_data="countries_0"),
        InlineKeyboardButton(text="🗺️ Регионы", callback_data="regions"),
        InlineKeyboardButton(text="🌎 Весь мир", callback_data="choose_plan_rub_global"),
    ], (1,))

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
        get_euro_to_rub_rate() if currency == 'RUB'
        else get_euro_to_rub_rate() / 1.5
    )

    # Рассчитываем цены для каждого плана
    prices = {}
    for plan in [3, 5, 10, 20]:
        price = float(price_data[plan]["price"])
        prices[plan] = int(price * multiplier * 1.04 * Config.PERCENT_OF_STONX)

    return prices


async def prepare_payment_order(callback: CallbackQuery, currency, is_top_up=False):
    admin_text = ""
    chat_id = str(callback.message.chat.id)
    admin_text += f"chat_id: {chat_id}\n"
    gb_amount = int(callback.data.split("_")[-1])
    admin_text += f"gb: {gb_amount}\n"
    if is_top_up:
        admin_text += f"top_up: {is_top_up}\n"
        db_update_top_up_flag_true(chat_id)
        country = db_get_top_up_data_country(chat_id)
        admin_text += f"country: {country}\n"
        db_update_top_up_data_volume(chat_id, gb_amount)
    else:
        admin_text += f"top_up: {is_top_up}\n"
        db_update_top_up_flag_false(chat_id)
        country = db_get_data_country(chat_id)
        admin_text += f"country: {country}\n"
        db_update_data_volume(chat_id, gb_amount)
    emoji = db_get_emoji_from_two_tables(country.replace("_", " "))
    admin_text += f"emoji: {emoji}\n"
    ru_name = db_get_ru_name_from_two_tables(country.replace("_", " "))
    admin_text += f"ru_name: {ru_name}\n"
    prices = get_plan_prices(currency, chat_id, is_top_up)
    admin_text += f"prices: {prices}\n"
    amount = prices[gb_amount]
    admin_text += f"amount: {amount}\n"
    photo_url = db_get_pay_pic_link(country)
    admin_text += f"currency: {currency}\n"
    if currency == "XTR":
        invoice_params = {
            'chat_id': callback.from_user.id,
            'title': f"Счет “{emoji}{ru_name.title()} - {gb_amount}GB”",
            'description': f"Вы выбрали тариф “{country.title()} - {gb_amount}”."
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
        await Config.BOT.send_message(chat_id="1547142782", text=admin_text)
        await Config.BOT.send_invoice(**invoice_params)
    else:
        digits = random.randint(3, 10)
        invoice_id = random.randint(10 ** (digits - 1), (10 ** digits) - 1)
        admin_text += f"invoice_id: {invoice_id}\n"
        username = db_get_username(chat_id)
        admin_text += f"username: {username}\n"
        db_save_invoice_user(invoice_id, chat_id, username, datetime.now())
        payment_link = generate_payment_link(Config.MERCHANT_LOGIN, Config.PASSWORD1, amount, invoice_id,
                                             f"{country} - {amount}", 0)
        admin_text += f"payment_link: {payment_link}\n"
        kb = InlineKeyboardBuilder().add(
            InlineKeyboardButton(text="💳 Оплатить", url=payment_link)
        ).as_markup()
        if photo_url:
            await Config.BOT.send_photo(chat_id=chat_id,
                                        photo=photo_url,
                                        caption=f"Вы выбрали тариф “{emoji}{ru_name.title()} - {gb_amount}GB”."
                                                f"\n\n⚠️ Учтите: активным для оплаты считается счет,"
                                                f" выставленный последним в диалоге.",
                                        reply_markup=kb,
                                        parse_mode="HTML")
            await Config.BOT.send_message(chat_id="1547142782", text=admin_text, parse_mode="HTML")
            await Config.BOT.send_photo(chat_id="1547142782",
                                        photo=photo_url,
                                        caption=f"Вы выбрали тариф “{emoji}{ru_name.title()} - {gb_amount}GB”."
                                                f"\n\n⚠️ Учтите: активным для оплаты считается счет,"
                                                f" выставленный последним в диалоге.",
                                        reply_markup=kb,
                                        parse_mode="HTML")
        else:
            await Config.BOT.send_message(chat_id=chat_id, text=f"Вы выбрали тариф"
                                                                f" “{emoji}{ru_name.title()} - {gb_amount}”."
                                                                f"\n\n⚠️ Учтите: активным для оплаты считается счет,"
                                                                f" выставленный последним в диалоге.",
                                          reply_markup=kb,
                                          parse_mode="HTML")
            await Config.BOT.send_message(chat_id="1547142782", text=admin_text, parse_mode="HTML")
            await Config.BOT.send_message(chat_id="1547142782", text=f"Вы выбрали тариф"
                                                                     f" “{emoji}{ru_name.title()} - {gb_amount}”."
                                                                     f"\n\n⚠️ Учтите: активным для оплаты считается счет,"
                                                                     f" выставленный последним в диалоге.",
                                          reply_markup=kb,
                                          parse_mode="HTML")


async def handle_first_payment_order(cli, chat_id, data, bnesim, downloading_message):
    product_id = db_get_product_id(data["country"], data["volume"])
    db_update_cli(chat_id, cli)
    active_esim = await bnesim.activate_esim(cli, product_id)
    esim_info = await bnesim.get_esim_info(active_esim["iccid"])
    while cli is None and active_esim["qr_code"] is None:
        await asyncio.sleep(1)
    db_clean_data(chat_id)
    await Config.BOT.delete_message(chat_id=chat_id, message_id=downloading_message.message_id)
    await Config.BOT.send_photo(chat_id=chat_id, photo=BufferedInputFile(active_esim["qr_code"],
                                                                         "png_qr_code.png"),
                                caption="*🎊 Поздравляем с приобретением вашей первой eSIM!*"
                                        "\n\n☎️ *Название вашей eSIM:*"
                                        f" `{data["country"].title()} - {active_esim['iccid'][-4:]}`"
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
        iccids_map = await bnesim.get_iccids_of_user(cli)
        if top_up_data["iccid"] in iccids_map["iccids"]:
            api_answer = await bnesim.top_up_existing_esim(cli, top_up_data["iccid"], product_id)
            db_clean_top_up_data(chat_id)
            while api_answer is None:
                await asyncio.sleep(1)
            await Config.BOT.delete_message(chat_id=chat_id, message_id=downloading_message.message_id)
            await Config.BOT.send_message(chat_id=chat_id, text="*🎊 Успешное продление eSIM!*"
                                                                f"\n\n*📛 Название вашей eSIM:*"
                                                                f" `{top_up_data["country"].title()} - {top_up_data["iccid"][-4:]}`"
                                                                f"\n\n🤖 Вы можете посмотреть инструкцию по установке и"
                                                                f" подробную информацию о ваших eSIM с помощью команды /get\_my\_esims")
    else:
        product_id = db_get_product_id(data["country"], data["volume"])
        active_esim = await bnesim.activate_esim(cli, product_id)
        esim_info = await bnesim.get_esim_info(active_esim["iccid"])
        while active_esim["qr_code"] is None:
            await asyncio.sleep(1)
        db_clean_data(chat_id)
        await Config.BOT.delete_message(chat_id=chat_id, message_id=downloading_message.message_id)
        await Config.BOT.send_photo(chat_id=chat_id, photo=BufferedInputFile(active_esim["qr_code"],
                                                                             "png_qr_code.png"),
                                    caption="🎊 Спасибо за приобретение новой eSIM!"
                                            "\n\n📛 *Название вашей eSIM:*"
                                            f" `{data["country"].title()} - {active_esim['iccid'][-4:]}`"
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
