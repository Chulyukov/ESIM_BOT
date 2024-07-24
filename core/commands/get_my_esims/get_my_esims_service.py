from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


async def get_my_esims_service(message: Message):
    # TODO: Разработать фича-флаг "есть 1+ esim или нет ни одной". Фича-флаг будет опираться на запрос
    #  "5.Customer Details - GET https://api.bnesim.com/v0.1/customer_details/?auth_token=%AUTH_TOKEN%
    #  &cli= %ACCOUNT_NUMBER%&events=5"

    # TODO: Добавить логику просмотра инфы (сколько осталось трафик и т.п.) существующей esim с помощью запроса 7

    kb = InlineKeyboardBuilder().add(
        InlineKeyboardButton(text="Приобрести esim", callback_data="buy_esim")
    ).as_markup()
    await message.answer(text="*💔 Мы не нашли у вас ни одной esim, но вы можете приобрести их, нажав кнопку ниже.*",
                         reply_markup=kb)
