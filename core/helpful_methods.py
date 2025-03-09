import asyncio
from io import BytesIO

import qrcode
from aiogram.utils.keyboard import InlineKeyboardBuilder

from currency_rate import get_dollar_to_rub_rate
from monty_api import MontyApiAsync


def get_username(message):
    """Получение имени пользователя."""
    return f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name


def build_keyboard(buttons, layout):
    """Создание клавиатуры с заданной раскладкой."""
    kb = InlineKeyboardBuilder()
    kb.add(*buttons)
    return kb.adjust(*layout).as_markup()


async def generate_qr_code(activation_code: str) -> BytesIO:
    """
    Асинхронно генерирует QR-код и возвращает его в виде объекта BytesIO.
    """
    def create_qr():
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(activation_code)
        qr.make(fit=True)

        buffer = BytesIO()
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

    # Асинхронный вызов генерации QR-кода
    return await asyncio.to_thread(create_qr)


async def get_bundle_price_list(country):
    """Получение цен для тарифов по стране."""
    multiplier = get_dollar_to_rub_rate()
    processed_bundle_data = {}

    monty = MontyApiAsync()
    bundle_data = await monty.get_bundle_data(country)

    for gb_amount in [3, 5, 10, 20]:
        bundle_price = 10000
        subscriber_price = ""
        bundle_code = ""
        for bundle in bundle_data:
            if ((f"{gb_amount}GB" in bundle["bundle_name"] or
                 f"{float(gb_amount) * 1024}MB" in bundle["bundle_name"]) and bundle_price > bundle["subscriber_price"]) and bundle["validity"] == 30:
                bundle_price = bundle["subscriber_price"]
                subscriber_price = bundle["subscriber_price"]
        if subscriber_price:
            processed_bundle_data[str(gb_amount)] = float(subscriber_price) * multiplier * 1.04 * 1.06 * 1.2 * 1.2 * 1.4

    return processed_bundle_data
