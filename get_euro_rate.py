import requests
from xml.etree import ElementTree as ET


def get_euro_to_rub_rate():
    url = "https://www.cbr.ru/scripts/XML_daily.asp"
    response = requests.get(url)
    response.raise_for_status()  # Проверяем успешность запроса

    # Парсинг XML-ответа
    tree = ET.fromstring(response.content)
    for currency in tree.findall("Valute"):
        if currency.find("CharCode").text == "EUR":
            rate = currency.find("Value").text.replace(",", ".")
            return float(rate) + 2
    raise ValueError("Курс евро не найден в ответе Центробанка")
