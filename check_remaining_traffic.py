import asyncio
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bnesim_api import BnesimApi
from config import Config
from db.db_queries import db_get_all_cli, db_get_hidden_esims

# Создание экземпляра API BNESIM
bnesim_api = BnesimApi()

# Получение списка пользователей с CLI
users_list = db_get_all_cli()


async def send_remaining_info():
    """Отправка уведомлений пользователям о заканчивающемся пакете интернета."""
    for user in users_list:
        chat_id, cli = user[0], user[1]
        hidden_esims = db_get_hidden_esims(chat_id)
        iccids_dict = bnesim_api.get_iccids_of_user(cli)

        if iccids_dict["length"] > 0:
            for iccid in iccids_dict["iccids"]:
                # Пропускаем скрытые eSIM
                if hidden_esims and iccid in hidden_esims.get("esims", []):
                    continue

                esim_info = bnesim_api.get_esim_info(iccid)

                # Если информация о eSIM есть и оставшийся трафик <= 1 ГБ
                if esim_info and esim_info['remaining_data'] <= 1.0:
                    kb = InlineKeyboardBuilder().add(
                        InlineKeyboardButton(text="Продлить интернет", callback_data="top_up_choose_payment_method_"),
                        InlineKeyboardButton(text="Удалить eSIM", callback_data=f"delete_esim_{iccid}"),
                    ).adjust(1).as_markup()

                    try:
                        await Config.BOT.send_message(
                            chat_id=chat_id,
                            text=(
                                f"🪫 У вас заканчивается пакет интернета"
                                f" на eSIM “`{esim_info['country']} - {iccid[-4:]}`”"
                                " (осталось меньше 1 ГБ)."
                                "\n\n👇 Нажмите соответствующую кнопку ниже,"
                                " чтобы продлить свой тариф или"
                                " *безвозвратно удалить* ненужную eSIM. Удаленная eSIM"
                                " перестанет отображаться в вашем списке, но"
                                " оставшийся интернет останется доступным."
                            ),
                            reply_markup=kb,
                        )
                    except Exception as e:
                        print(f"Ошибка при отправке сообщения пользователю chat_id={chat_id}: {e}")


# Запуск функции отправки уведомлений
if __name__ == "__main__":
    asyncio.run(send_remaining_info())