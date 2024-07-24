from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup
from aiogram.types import CallbackQuery


async def remember_country(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    country = user_data.get('country', None)

    if country is None or country == '':
        await state.update_data(country=callback.data[callback.data.rfind('_') + 1:])


class Status(StatesGroup):
    country: str = None
    payment_method: str = None
