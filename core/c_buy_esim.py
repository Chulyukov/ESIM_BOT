from aiogram import Router, F, types
from aiogram.enums import ContentType
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton

from bnesim_api import BnesimApi
from config import Config
from core.helpful_methods import get_username, get_plan_prices, build_keyboard, prepare_payment_order, \
    handle_payment_order, handle_first_payment_order, choose_direction
from db.countries.db_countries import db_get_20_countries
from db.db_buy_esim import db_get_emoji_from_two_tables, db_get_ru_name_from_two_tables
from db.regions.regions import db_get_regions
from db.users.db_cli import db_get_cli
from db.users.db_data import db_update_data_country, db_get_all_data
from db.users.db_top_up_data import db_get_all_top_up_data, db_get_top_up_flag

router = Router()


@router.callback_query(F.data == "buy_esim")
@router.message(Command("buy_esim"))
async def buy_esim(msg: Message | CallbackQuery):
    await choose_direction(msg)


@router.callback_query(F.data == "popular_directions")
async def choose_popular_direction(callback: CallbackQuery):
    kb = build_keyboard([
        InlineKeyboardButton(text="🇹🇷 Турция", callback_data="choose_plan_rub_turkey"),
        InlineKeyboardButton(text="🇹🇭 Тайланд", callback_data="choose_plan_rub_thailand"),
        InlineKeyboardButton(text="🇦🇪 Объединенные Арабские Эмираты", callback_data="choose_plan_rub_united_arab_emirates"),
        InlineKeyboardButton(text="🇪🇬 Египет", callback_data="choose_plan_rub_egypt"),
        InlineKeyboardButton(text="🇬🇷 Греция", callback_data="choose_plan_rub_greece"),
        InlineKeyboardButton(text="🇻🇳 Вьетнам", callback_data="choose_plan_rub_vietnam"),
        InlineKeyboardButton(text="🇪🇸 Испания", callback_data="choose_plan_rub_spain"),
        InlineKeyboardButton(text="🇮🇩 Индонезия", callback_data="choose_plan_rub_indonesia"),
        InlineKeyboardButton(text="🇨🇳 Китай", callback_data="choose_plan_rub_china"),
        InlineKeyboardButton(text="🇨🇾 Кипр", callback_data="choose_plan_rub_cyprus"),
        InlineKeyboardButton(text="⏪ К выбору направлений", callback_data="buy_esim"),
    ], (2, 2, 2, 2, 2, 1))
    await callback.message.edit_text(
        text="\n\n🆘 Если у вас возникли какие-либо сложности, пожалуйста, свяжитесь со [службой заботы клиента](https://t.me/esim_unity_support)."
             "\n\n*👇 Выберите конкретное направление.*",
        reply_markup=kb,
        disable_web_page_preview=True)


@router.callback_query(F.data.startswith("countries_"))
async def choose_concrete_direction(callback: CallbackQuery):
    pages_to_skip = int(callback.data[-1])
    countries = db_get_20_countries(pages_to_skip)
    next_countries = db_get_20_countries(pages_to_skip + 1)
    buttons = [
        InlineKeyboardButton(
            text=f"{emoji} {ru_name.title()}",
            callback_data=f"choose_plan_rub_{name.replace(' ', '_')}"
        )
        for name, ru_name, emoji in countries
    ]

    if pages_to_skip > 0 and len(next_countries) != 0:
        buttons.append(InlineKeyboardButton(text="⏮️ Назад", callback_data=f"countries_{str(pages_to_skip - 1)}"))
        buttons.append(InlineKeyboardButton(text="⏭️ Дальше", callback_data=f"countries_{str(pages_to_skip + 1)}"))
        buttons.append(InlineKeyboardButton(text="⏪ К выбору направлений", callback_data="buy_esim"))
        kb = build_keyboard(buttons, (2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1))
    elif pages_to_skip > 0 and len(next_countries) == 0:
        buttons.append(InlineKeyboardButton(text="⏮️ Назад", callback_data=f"countries_{str(pages_to_skip - 1)}"))
        buttons.append(InlineKeyboardButton(text="⏪ К выбору направлений", callback_data="buy_esim"))
        kb = build_keyboard(buttons, (2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1))
    else:
        buttons.append(InlineKeyboardButton(text="⏭️ Дальше", callback_data=f"countries_{str(pages_to_skip + 1)}"))
        buttons.append(InlineKeyboardButton(text="⏪ К выбору направлений", callback_data="buy_esim"))
        kb = build_keyboard(buttons, (2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1))
    await callback.message.edit_text(
        text="🆘 Если у вас возникли какие-либо сложности, пожалуйста, свяжитесь со [службой заботы клиента](https://t.me/esim_unity_support)."
             "\n\n*👇 Выберите страну.*",
        reply_markup=kb,
        disable_web_page_preview=True)


@router.callback_query(F.data == "regions")
async def choose_region(callback: CallbackQuery):
    regions = db_get_regions()
    buttons = [
        InlineKeyboardButton(
            text=f"{emoji} {ru_name.title()}",
            callback_data=f"choose_plan_rub_{name.replace(' ', '_')}"
        )
        for name, ru_name, emoji in regions
    ]
    buttons.append(InlineKeyboardButton(text="⏪ К выбору направлений", callback_data="buy_esim"))
    kb = build_keyboard(buttons, (1,))

    await callback.message.edit_text(
        text="*🌍 Узнайте, какие страны входят в региональные пакеты с интернетом в формате eSIM.*"
             "\nЭто поможет вам оставаться на связи в разных частях мира без лишних сложностей!"
             "\n\n*📱 Подробности в нашей статье по ссылке:*"
             "\n[Пакеты eSIM для разных регионов: доступные страны](https://telegra.ph/Pakety-eSIM-dlya-raznyh-regionov-dostupnye-strany-10-06)"
             "\n\n🆘 Если у вас возникли какие-либо сложности, пожалуйста, свяжитесь со [службой заботы клиента](https://t.me/esim_unity_support)."
             "\n\n*✈️ Ознакомьтесь с доступными странами и выберите лучший пакет для вашего путешествия!*",
        reply_markup=kb, disable_web_page_preview=True)


@router.callback_query(F.data == "search")
async def search(callback: CallbackQuery):
    await callback.message.answer("⌨️ В поле ввода сообщения вы можете ввести название интересующего вас направления.")


# @router.callback_query(F.data.startswith("choose_payment_method_"))
# async def choose_payment_method(callback: CallbackQuery):
#     country = callback.data.split("choose_payment_method_")[1]
#     emoji = db_get_emoji_from_two_tables(country.replace("_", " "))
#     ru_name = db_get_ru_name_from_two_tables(country.replace("_", " "))
#     text = (f"*📍 Выбранное направление - *`{emoji}{ru_name.title()}`"
#             f"\n\n*👇 Выберите способ оплаты.*")
#     if country == "global":
#         text = ("*🌍 Хотите узнать, как подключиться к интернету с помощью eSIM в разных странах мира?* Ознакомьтесь с нашей статьей, в которой подробно расписаны страны, входящие в глобальные eSIM-пакеты, и особенности подключения."
#             "\n\n*📱 Подробности читайте здесь:*"
#             "\n[Глобальные eSIM-пакеты: Страны и особенности подключения](https://telegra.ph/Globalnye-eSIM-pakety-Strany-i-osobennosti-podklyucheniya-10-06)"
#             "\n\n🆘 Если у вас возникли какие-либо сложности, пожалуйста, свяжитесь со [службой заботы клиента](https://t.me/esim_unity_support)."
#             "\n\n*✈️ Путешествуйте с комфортом и всегда оставайтесь на связи!*")
#     db_update_data_country(callback.message.chat.id, callback.data.split("_")[-1])
#     buttons = [
#         InlineKeyboardButton(text="💳 Российская карта", callback_data=f"choose_plan_rub_{country}"),
#         InlineKeyboardButton(text="⭐️ Telegram Stars", callback_data=f"choose_plan_star_{country}"),
#         InlineKeyboardButton(text="⏪ К выбору направлений", callback_data="buy_esim")
#     ]
#     kb = build_keyboard(buttons, (1,))
#     await callback.message.edit_text(text=text,
#                                      reply_markup=kb,
#                                      disable_web_page_preview=True)


@router.callback_query(F.data.startswith("choose_plan_rub_"))
async def choose_plan_rub(callback: CallbackQuery):
    country = callback.data.split("choose_plan_rub_")[1]
    db_update_data_country(callback.message.chat.id, country.replace("_", " "))
    prices = get_plan_prices("RUB", callback.message.chat.id)
    buttons = [
        InlineKeyboardButton(text=f"{gb} ГБ - {price} RUB", callback_data=f"pay_rub_{gb}")
        for gb, price in prices.items()
    ]
    buttons.append(InlineKeyboardButton(text="⏪ К выбору направлений", callback_data="buy_esim"))
    kb = build_keyboard(buttons, (2, 2, 1))
    await callback.message.edit_text(text="💳 Оплачивая российской картой, вы соглашаетесь с"
                                          " [условиями использования сервиса](https://telegra.ph/Kak-proishodit-oplata-v-bote-09-05)."
                                          "\n\n🆘 Если у вас возникли какие-либо сложности, пожалуйста, свяжитесь со [службой заботы клиента](https://t.me/esim_unity_support)."
                                          "\n\n*👇 Выберите интересующий вас пакет интернета.*",
                                     reply_markup=kb,
                                     disable_web_page_preview=True)


# @router.callback_query(F.data.startswith("choose_plan_star_"))
# async def choose_plan_star_card(callback: CallbackQuery):
#     country = callback.data.split("choose_plan_star_")[1]
#     db_update_data_country(callback.message.chat.id, country.replace("_", " "))
#     prices = get_plan_prices("XRT", callback.message.chat.id)
#     buttons = [
#         InlineKeyboardButton(text=f"{gb} ГБ - {price} STARS", callback_data=f"pay_stars_{gb}")
#         for gb, price in prices.items()
#     ]
#     buttons.append(InlineKeyboardButton(text="⏪ Назад", callback_data=f"choose_payment_method_{country}"))
#     kb = build_keyboard(buttons, (2, 2, 1))
#     await callback.message.edit_text(
#         text="🆘 Если у вас возникли какие-либо сложности, пожалуйста, свяжитесь со [службой заботы клиента](https://t.me/esim_unity_support)."
#              "\n\n*👇 Выберите интересующий вас пакет интернета.*",
#         reply_markup=kb,
#         disable_web_page_preview=True)


@router.callback_query(F.data.startswith("pay_rub_"))
async def pay_rub(callback: CallbackQuery):
    await prepare_payment_order(callback, "RUB")


# @router.callback_query(F.data.startswith("pay_stars_"))
# async def pay_star(callback: CallbackQuery):
#     await prepare_payment_order(callback, "XTR")


# @router.pre_checkout_query(lambda query: True)
# async def pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
#     await Config.BOT.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
#
#
# @router.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
# async def successful_payment(message: types.Message):
#     chat_id = message.chat.id
#     bnesim = BnesimApi()
#     cli = db_get_cli(chat_id)
#     data = db_get_all_data(chat_id)
#     top_up_data = db_get_all_top_up_data(chat_id)
#     downloading_message = await message.answer("*🚀 Подождите, обрабатываю данные платежа...*")
#     iccids_list = bnesim.get_iccids_of_user(cli)
#     top_up_flag = db_get_top_up_flag(chat_id)
#     if cli is None:
#         cli = bnesim.activate_user(f"{get_username(message)}_{chat_id}")
#         await handle_first_payment_order(cli, chat_id, data, bnesim, downloading_message)
#     else:
#         await handle_payment_order(cli, bnesim, data, top_up_data,
#                                    top_up_flag, chat_id, downloading_message, iccids_list)
#
#     await handle_payment_order(cli, bnesim, data, top_up_data, top_up_flag, chat_id, downloading_message, iccids_list)
