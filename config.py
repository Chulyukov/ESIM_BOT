from dataclasses import dataclass
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties


@dataclass
class Config:
    """Конфигурационный класс для хранения настроек приложения."""

    # Токены телеграм-ботов
    TOKEN: str = "7210348872:AAGDZsDcTsAszxGEhCNBCmmZkbSRC5n868c"
    TEST_TOKEN: str = "8101981246:AAGwNiazPZliWFFMItehFeFO8HCQ0fgIUJA"

    # Создание объекта бота
    BOT: Bot = Bot(TEST_TOKEN, default=DefaultBotProperties(parse_mode='MARKDOWN'))

    # Ссылки на бота
    BOT_LINK: str = "https://t.me/esim_unity_bot"

    # BNESIM креденшиалы
    BNESIM_PARTNER_LOGIN: str = "nikita.admin"
    BNESIM_API_KEY: str = "pe2mp9qxcen9"

    # Настройки базы данных
    DB_HOST: str = "213.108.20.201"
    DB_NAME: str = "esim_db"
    DB_USER: str = "esim_user"
    DB_PASS: str = "Kexibq528123!"

    # Полезные ссылки
    QUESTIONS_LINK: str = "https://telegra.ph/CHto-takoe-eSIM-07-27"
    SUPPORT_LINK: str = "https://t.me/esim_unity_support"
    SUPPORT_SIMPLE_LINK: str = "@esim_unity_support"
    CHANNEL_LINK: str = "https://t.me/esim_unity"

    # Robokassa настройки
    API_TOKEN: str = TOKEN
    WEBHOOK_HOST: str = "https://esimunity.ru"
    WEBHOOK_PATH: str = "/payment-result"
    WEBHOOK_URL: str = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
    MERCHANT_LOGIN: str = "esimUnityTg"

    # Пароли Robokassa
    TEST_PASSWORD1: str = "g26216mIRpoFvgKuWROg"
    TEST_PASSWORD2: str = "xC74cTl3pe7Lr8IxVTzd"
    PASSWORD1: str = "O0aeVibKLOm5d2CO8R5t"
    PASSWORD2: str = "YaTobt46ilslW7eO07mU"