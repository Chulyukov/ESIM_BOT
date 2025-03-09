from xml.etree import ElementTree as ET

import requests


def get_dollar_to_rub_rate():
    """
    Получение курса доллара к рублю с сайта Центробанка РФ.

    Returns:
        float: Курс доллара с добавлением надбавки в 4 рубля.

    Raises:
        ValueError: Если курс доллара не найден в XML-ответе.
        requests.RequestException: Если запрос не удался.
    """
    url = "https://www.cbr.ru/scripts/XML_daily.asp"
    try:
        # Выполнение запроса к API Центробанка
        response = requests.get(url)
        response.raise_for_status()

        # Парсинг XML-ответа
        tree = ET.fromstring(response.content)
        for currency in tree.findall("Valute"):
            if currency.find("CharCode").text == "USD":
                # Конвертация значения курса в float и добавление надбавки
                rate = float(currency.find("Value").text.replace(",", "."))
                return rate + 4

        # Если валюта EUR не найдена
        raise ValueError("Курс доллара не найден в ответе Центробанка")

    except requests.RequestException as e:
        print(f"Ошибка запроса к API Центробанка: {e}")
        raise