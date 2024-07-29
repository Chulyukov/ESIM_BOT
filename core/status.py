from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery


async def remember_country(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    country = user_data.get('country', None)

    if country is None or country == '':
        await state.update_data(country=callback.data[callback.data.rfind('_') + 1:])


async def remember_iccid(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    country = user_data.get('iccid', None)

    if country is None or country == '':
        await state.update_data(iccid=callback.data[callback.data.rfind('_') + 1:])


class Status(StatesGroup):
    iccid: str = None
    country: str = None
    volume: int = None
    payment_method: str = None
