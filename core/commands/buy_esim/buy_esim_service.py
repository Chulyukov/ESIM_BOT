from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import Config


async def buy_esim_service(msg: Message | CallbackQuery):
    kb = InlineKeyboardBuilder().add(
        InlineKeyboardButton(text="🇹🇷Турция", callback_data="choose_payment_method_turkey"),
        InlineKeyboardButton(text="🇦🇪ОАЭ", callback_data="choose_payment_method_uae"),
        InlineKeyboardButton(text="🇹🇭Тайланд", callback_data="choose_payment_method_thailand"),
        InlineKeyboardButton(text="🇬🇪Грузия", callback_data="choose_payment_method_georgia"),
        InlineKeyboardButton(text="🇪🇬Египет", callback_data="choose_payment_method_egypt"),
    ).adjust(1, 2).as_markup()

    message_text = ("Перед тем, как выбрать страну,"
                    " *обязательно проверьте возможность установки esim на маш смартфон*."
                    "\nСписок девайсов, поддерживающих данную функцию,"
                    " вы найдете по ссылке: *ссылка на Telegraph*"
                    "\n\n👇*Выберите одну из доступных стран.*")

    if isinstance(msg, CallbackQuery):
        await msg.message.edit_text(text=message_text, reply_markup=kb, disable_web_page_preview=True)
    elif isinstance(msg, Message):
        await msg.answer(text=message_text, reply_markup=kb, disable_web_page_preview=True)


async def choose_payment_method_service(callback: CallbackQuery):
    kb = InlineKeyboardBuilder().add(
        InlineKeyboardButton(text="💳 Российская карта", callback_data="choose_plan_russian_card"),
        InlineKeyboardButton(text="⭐️ Telegram Stars", callback_data="choose_plan_star"),
        InlineKeyboardButton(text="⏪ Назад", callback_data="buy_esim"),
    ).adjust(1).as_markup()
    await callback.message.edit_text("*Выберите способ оплаты.*", reply_markup=kb)


async def choose_plan_russian_service(callback: CallbackQuery):
    kb = InlineKeyboardBuilder().add(
        InlineKeyboardButton(text=f"1 ГБ - {Config.PRICE_1_GB_RUB} RUB", callback_data="pay_russian_card_1"),
        InlineKeyboardButton(text=f"3 ГБ - {Config.PRICE_3_GB_RUB} RUB", callback_data="pay_russian_card_3"),
        InlineKeyboardButton(text=f"5 ГБ - {Config.PRICE_5_GB_RUB} RUB", callback_data="pay_russian_card_5"),
        InlineKeyboardButton(text=f"10 ГБ - {Config.PRICE_10_GB_RUB} RUB", callback_data="pay_russian_card_10"),
        InlineKeyboardButton(text=f"20 ГБ - {Config.PRICE_20_GB_RUB} RUB", callback_data="pay_russian_card_20"),
        InlineKeyboardButton(text="⏪ Назад", callback_data="choose_payment_method_"),
    ).adjust(2, 2, 1, 1).as_markup()
    await callback.message.edit_text(text="*Выберите интересующий вас набор интернет-трафика.*", reply_markup=kb)


async def choose_plan_star_service(callback: CallbackQuery):
    kb = InlineKeyboardBuilder().add(
        InlineKeyboardButton(text=f"1 ГБ - {Config.PRICE_1_GB_STAR} STARS", callback_data="pay_star_1"),
        InlineKeyboardButton(text=f"3 ГБ - {Config.PRICE_3_GB_STAR} STARS", callback_data="pay_star_3"),
        InlineKeyboardButton(text=f"5 ГБ - {Config.PRICE_5_GB_STAR} STARS", callback_data="pay_star_5"),
        InlineKeyboardButton(text=f"10 ГБ - {Config.PRICE_10_GB_STAR} STARS", callback_data="pay_star_10"),
        InlineKeyboardButton(text=f"20 ГБ - {Config.PRICE_20_GB_STAR} STARS", callback_data="pay_star_20"),
        InlineKeyboardButton(text="⏪ Назад", callback_data="choose_payment_method_"),
    ).adjust(2, 2, 1, 1).as_markup()
    await callback.message.edit_text(text="*Выберите интересующий вас набор интернет-трафика.*", reply_markup=kb)


async def pay_russian_card_service(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    gb_amount = callback.data[callback.data.rfind("_") + 1:]
    if gb_amount == "1":
        amount = Config.PRICE_1_GB_RUB
    elif gb_amount == "3":
        amount = Config.PRICE_3_GB_RUB
    elif gb_amount == "5":
        amount = Config.PRICE_5_GB_RUB
    elif gb_amount == "10":
        amount = Config.PRICE_10_GB_RUB
    else:
        amount = Config.PRICE_20_GB_RUB
    prices = [
        types.LabeledPrice(label="Оплата esim российской картой", amount=amount * 100)
    ]
    await Config.BOT.send_invoice(
        callback.from_user.id,
        title=f"{user_data["country"].capitalize()} - {gb_amount}GB",
        description="Вы приобретаете указанный ранее пакет интернета"
                    " в выбранной вами стране с помощью российской карты.",
        provider_token=Config.YUKASSA_LIVE_TOKEN,
        currency="rub",
        photo_url="https://i.imgur.com/MOnD80s.jpeg",
        photo_width=416,
        photo_height=234,
        is_flexible=False,
        prices=prices,
        payload="test-invoice-payload",
        need_email=True,
        send_email_to_provider=True,
        provider_data=f"{{'receipt': {{'customer': {{'email': 'hipstakrippo@gmail.com'}},'items': [{{'description': '',"
                      f"'amount': {{'value': '{amount}', "
                      f"'currency': 'RUB'}},'vat_code': 1,'quantity'': 1}}]}}}}",
    )


async def pay_star_service(callback: CallbackQuery, state: FSMContext):
    # TODO: Разобраться, куда же все-таки звезды клиента после оплаты XD
    user_data = await state.get_data()
    gb_amount = callback.data[callback.data.rfind("_") + 1:]
    if gb_amount == "1":
        amount = Config.PRICE_1_GB_STAR
    elif gb_amount == "3":
        amount = Config.PRICE_3_GB_STAR
    elif gb_amount == "5":
        amount = Config.PRICE_5_GB_STAR
    elif gb_amount == "10":
        amount = Config.PRICE_10_GB_STAR
    else:
        amount = Config.PRICE_20_GB_STAR
    prices = [
        types.LabeledPrice(label="Оплата esim с помощью Telegram Stars", amount=amount)
    ]
    await Config.BOT.send_invoice(
        callback.from_user.id,
        title=f"{user_data["country"].capitalize()} - {gb_amount}GB",
        description="Вы приобретаете указанный ранее пакет интернета"
                    " в выбранной вами стране с помощью Telegram Stars.",
        provider_token="",
        currency="XTR",
        photo_url="https://i.imgur.com/MOnD80s.jpeg",
        photo_width=416,
        photo_height=234,
        is_flexible=False,
        prices=prices,
        payload="test-invoice-payload",
    )
