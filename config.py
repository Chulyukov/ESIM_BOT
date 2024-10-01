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
    DB_USER = "esim_user"
    DB_PASS = "Kexibq528123!"
    # Ссылка на популярные вопросы в Telegraph
    QUESTIONS_LINK = "https://telegra.ph/CHto-takoe-eSIM-07-27"
    # Ссылка на саппорта
    SUPPORT_LINK = "https://t.me/esim_unity_support"
    SUPPORT_SIMPLE_LINK = "@esim\_unity\_support"
    # Ссылка на канал
    CHANNEL_LINK = "https://t.me/esim_unity"
    # YOKASSA TOKEN
    YUKASSA_LIVE_TOKEN = "390540012:LIVE:36227"
    # Процент наценки
    PERCENT_OF_STONX = 1.20
    # Курс евро
    EURO_EXCHANGE_RATE = 102
    # Robokassa
    API_TOKEN = '7210348872:AAGDZsDcTsAszxGEhCNBCmmZkbSRC5n868c'
    WEBHOOK_HOST = 'https://esimunity.ru'
    WEBHOOK_PATH = '/payment-result'
    WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

    MERCHANT_LOGIN = 'esimUnityTg'
    TEST_PASSWORD1 = 'g26216mIRpoFvgKuWROg'
    TEST_PASSWORD2 = 'xC74cTl3pe7Lr8IxVTzd'
    PASSWORD1 = 'O0aeVibKLOm5d2CO8R5t'
    PASSWORD2 = 'YaTobt46ilslW7eO07mU'
