from dataclasses import dataclass

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties


@dataclass
class Config:
    # Токен телеграм-бота t.me/esim_unity_bot
    TOKEN = "7210348872:AAGDZsDcTsAszxGEhCNBCmmZkbSRC5n868c"
    # Токен тестового телеграм-бота t.me/vdghasda_bot
    TEST_TOKEN = "7454139393:AAGvzYI_Jlmeq9oijARYzPlBoRJOfbaqytE"
    # Сущность бота
    BOT = Bot(TOKEN, default=DefaultBotProperties(parse_mode='MARKDOWN'))
    # Тестовый токен YOKASSA
    YOKASSA_TEST_TOKEN = "381764678:TEST:91407"
    # BNESIM креды
    BNESIM_PARTNER_LOGIN = "nikita.admin"
    BNESIM_API_KEY = "pe2mp9qxcen9"
    # БД
    DB_HOST = "94.131.115.240"
    DB_NAME = "esim_db"
    DB_USER = "root"
    DB_PASS = "kexibq528123"
    # Ссылка на популярные вопросы в Telegraph
    QUESTIONS_LINK = "https://telegra.ph/CHto-takoe-eSIM-07-27"
    # Ссылка на саппорта
    SUPPORT_LINK = "https://t.me/esim_unity_support"
    SUPPORT_SIMPLE_LINK = "@esim\_unity\_support"
    # Ссылка на канал
    CHANNEL_LINK = "https://t.me/esim_unity"
    # YOKASSA TOKEN
    YUKASSA_LIVE_TOKEN = "390540012:LIVE:36227"
    # Курс евро
    EURO_EXCHANGE_RATE = 99
