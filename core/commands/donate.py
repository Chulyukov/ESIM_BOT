import json

from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import Config

router = Router()


@router.message(Command("donate"))
@router.callback_query(F.data == "donate")
async def donate(msg: Message | CallbackQuery):
    kb = InlineKeyboardBuilder().add(
        InlineKeyboardButton(text="💳 Российская карта", callback_data=f"donate_choose_amount_rub"),
        InlineKeyboardButton(text="⭐️ Telegram Stars", callback_data=f"donate_choose_amount_stars"),
    ).adjust(1).as_markup()
    if isinstance(msg, CallbackQuery):
        await msg.message.edit_text("*🎗️ Здесь вы можете сделать пожертвование на развитие нашего проекта."
                                    "\n🙏 Ваш вклад особенно ценен для нас.*",
                                    reply_markup=kb)
    else:
        await msg.answer(text="*🎗️ Здесь вы можете сделать пожертвование на развитие нашего проекта."
                              "\n🙏 Ваш вклад особенно ценен для нас.*",
                            reply_markup=kb)


@router.callback_query(F.data.startswith("donate_choose_amount_"))
async def donate_choose_amount(callback: CallbackQuery):
    if callback.data.endswith("rub"):
        kb = InlineKeyboardBuilder().add(
            InlineKeyboardButton(text="111 RUB", callback_data="donate_pay_111_rub"),
            InlineKeyboardButton(text="222 RUB", callback_data="donate_pay_222_rub"),
            InlineKeyboardButton(text="333 RUB", callback_data="donate_pay_333_rub"),
            InlineKeyboardButton(text="444 RUB", callback_data="donate_pay_444_rub"),
        )
    else:
        kb = InlineKeyboardBuilder().add(
            InlineKeyboardButton(text="111 STARS", callback_data="donate_pay_111_stars"),
            InlineKeyboardButton(text="222 STARS", callback_data="donate_pay_222_stars"),
            InlineKeyboardButton(text="333 STARS", callback_data="donate_pay_333_stars"),
            InlineKeyboardButton(text="444 STARS", callback_data="donate_pay_444_stars"),
        )
    kb = kb.add(InlineKeyboardButton(text="⏪ Назад", callback_data="donate")).adjust(2, 2, 1).as_markup()
    await callback.message.edit_text(text="*👇 Пожалуйста, выберите сумму для пожертвования.*", reply_markup=kb)


@router.callback_query(F.data.startswith("donate_pay_"))
async def donate_pay(callback: CallbackQuery):
    amount = int(callback.data.split("_")[-2])
    currency = callback.data.split("_")[-1].title()

    invoice_params = {
        'chat_id': callback.from_user.id,
        'title': f"Поддержка для проекта eSIM Unity - {amount} {currency}",
        'description': f"😇😇😇",
        'provider_token': Config.YOKASSA_TEST_TOKEN if currency == 'RUB' else '',
        'currency': 'rub' if currency == 'RUB' else 'XTR',
        # 'photo_url': "https://drive.google.com/file/d/1OYhHtsjpDgw40_l2nw47fQnav_oDDMAS/view?usp=sharing",
        # 'photo_width': 416,
        # 'photo_height': 416,
        'is_flexible': False,
        'prices': [types.LabeledPrice(label=f"eSIM payment using {currency}", amount=amount * 100 if currency == 'RUB' else amount)],
        'payload': "test-invoice-payload"
    }

    if currency == 'RUB':
        invoice_params.update({
            'need_email': True,
            'send_email_to_provider': True,
            'provider_data': json.dumps({
                'receipt': {
                    'customer': {'email': 'hipstakrippo@gmail.com'},
                    'items': [{
                        'description': 'Donation',
                        'amount': {'value': str(amount), 'currency': 'RUB'},
                        'vat_code': 1,
                        'quantity': 1
                    }]
                }
            })
        })
    await Config.BOT.send_invoice(**invoice_params)
