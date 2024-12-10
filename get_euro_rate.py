import requests
from xml.etree import ElementTree as ET


def get_euro_to_rub_rate():
    """
    Получение курса евро к рублю с сайта Центробанка РФ.

    Returns:
        float: Курс евро с добавлением надбавки в 2 рубля.

    Raises:
        ValueError: Если курс евро не найден в XML-ответе.
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
            if currency.find("CharCode").text == "EUR":
                # Конвертация значения курса в float и добавление надбавки
                rate = float(currency.find("Value").text.replace(",", "."))
                return rate + 2

        # Если валюта EUR не найдена
        raise ValueError("Курс евро не найден в ответе Центробанка")

    except requests.RequestException as e:
        print(f"Ошибка запроса к API Центробанка: {e}")
        raise