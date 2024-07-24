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
    # БД
    DB_HOST = "localhost"
    DB_NAME = "esim_db"
    DB_USER = "root"
    DB_PASS = "kexibq528123"
    # Ссылка на популярные вопросы в Telegraph
    QUESTIONS_LINK = ""
    # Ссылка на саппорта
    SUPPORT_LINK = "@esim\_unity\_support"
    # Ссылка на канал
    CHANNEL_LINK = "@esim\_unity"
    # YOKASSA TOKEN
    YUKASSA_LIVE_TOKEN = "390540012:LIVE:36227"
    # Наценка для русской карты
    PRICE_1_GB_RUB = 199
    PRICE_3_GB_RUB = 249
    PRICE_5_GB_RUB = 499
    PRICE_10_GB_RUB = 699
    PRICE_20_GB_RUB = 999
    # Наценка для звезд
    PRICE_1_GB_STAR = 10
    PRICE_3_GB_STAR = 25
    PRICE_5_GB_STAR = 40
    PRICE_10_GB_STAR = 85
    PRICE_20_GB_STAR = 180
