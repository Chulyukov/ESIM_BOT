import re
from io import BytesIO
import requests

from config import Config
from db.db_queries import db_insert_bnesim_products


class BnesimApi:
    """Класс для взаимодействия с API Bnesim."""

    def __init__(self):
        self.session = requests.Session()
        self.headers = {"accept": "*/*"}
        self.base_url = "https://api.bnesim.com/v0.1"
        self.auth_token = self._get_auth_token()

    def _request(self, method: str, path: str, **kwargs) -> dict:
        """Общий метод для выполнения запросов к API."""
        url = f"{self.base_url}{path}"
        try:
            response = self.session.request(method, url, verify=False, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Request to {url} failed: {e}")
            return {}

    def _get(self, path: str, **kwargs) -> dict:
        """Метод для выполнения GET-запросов."""
        return self._request("GET", path, **kwargs)

    def _get_auth_token(self) -> str:
        """Получение токена авторизации."""
        response = self._get(
            f"/auth_request/?partner_login={Config.BNESIM_PARTNER_LOGIN}&api_key={Config.BNESIM_API_KEY}&context=admin"
        )
        return response.get("auth_token") or print("Failed to retrieve auth token")

    def get_products_catalog(self) -> dict:
        """Получение каталога продуктов."""
        product_list = self._get("/partners_pricing/?format=json&a=928G")
        patterns = [
            r"^Surf (3|5|10|20)+GB in [A-Za-z0-9 ]+ (for|per) 30 days$",
            r"^Surf (3|5|10|20)+GB (for|per) 30 days in [A-Za-z0-9 ]+$",
            r"^Surf (3|5|10|20)+GB/30 days in [A-Za-z0-9 ]+$"
        ]
        country_pattern = r" in (.*?) (for|per) "
        new_data = {}

        for product in product_list:
            product_name = product["product_name"]
            if any(re.match(pattern, product_name) for pattern in patterns):
                country = self._extract_country(product_name, country_pattern)
                new_data[product["id"]] = {
                    "country": country,
                    "volume": product["volume"],
                    "price": float(product["price"]),
                }

        db_insert_bnesim_products(new_data)
        return new_data

    @staticmethod
    def _extract_country(product_name: str, country_pattern: str) -> str:
        """Извлечение страны из имени продукта."""
        match = re.search(country_pattern, product_name)
        return match.group(1).strip().lower() if match else product_name.split(" in ")[-1].lower()

    def activate_user(self, username: str) -> str:
        """Активация пользователя."""
        if not self.auth_token:
            print("No auth token available for activating user")
            return None
        user = self._get(f"/license_activation/?auth_token={self.auth_token}&name={username}&plan=254")
        return user.get("cli")

    def activate_esim(self, cli: str, product_id: int) -> dict:
        """Активация eSIM."""
        if not self.auth_token:
            print("No auth token available for activating eSIM")
            return None
        esim = self._get(
            f"/sim_card_customer_activation/?auth_token={self.auth_token}&action=activate-esim&cli={cli}&plan={product_id}"
        )
        return {
            "iccid": esim["iccid"],
            "qr_code": BytesIO(requests.get(esim["qr_code_url"]).content).read(),
            "qr_code_url": esim["qr_code_url"],
            "ios_universal_installation_link": esim["ios_universal_installation_link"],
        }

    def get_iccids_of_user(self, cli: str) -> dict:
        """Получение списка ICCID пользователя."""
        if not self.auth_token:
            print("No auth token available for getting ICCIDs")
            return {}
        response = self._get(
            f"/customer_details/?auth_token={self.auth_token}&cli={cli}&events=5&with_products=0"
        )
        simcards = response.get("customer_details", {}).get("simcards", [])
        return {
            "length": len(simcards),
            "iccids": [sim.get("iccid") for sim in simcards],
        }

    def get_esim_info(self, iccid: str) -> dict:
        """Получение информации об eSIM."""
        if not self.auth_token:
            print("No auth token available for getting eSIM info")
            return {}
        response = self._get(
            f"/sim_cards/?auth_token={self.auth_token}&action=get-details&iccid={iccid}&with_products=0"
        )
        if not response:
            print(f"No data available for ICCID {iccid}")
            return {}

        simcard_details = response["simcard_details"]
        return self._parse_esim_info(simcard_details)

    @staticmethod
    def _parse_esim_info(details: dict) -> dict:
        """Парсинг данных об eSIM."""
        if not details.get("data_credit_verbose"):
            return {}

        country = re.search(
            r"<b>[\d,]+\.\d+ MB</b> in (.+?)(?: valid till \d{2}/\d{2}/\d{4})?<br>", details["data_credit_verbose"]
        ).group(1).strip()
        first_key = next(iter(details["data_credit_details"]))
        second_key = next(iter(details["data_credit_details"][first_key]))
        volume_data = details["data_credit_details"][first_key][second_key]

        return {
            "ios_link": details["ios_universal_installation_link"],
            "volume": round(volume_data["associated_product"]["volume"] / 1024, 2),
            "country": country,
            "remaining_data": round(volume_data["remaining_mb"] / 1024, 2),
            "qr_code_image": BytesIO(requests.get(details["qr_code_image"]).content).read(),
            "qr_code_url": details["qr_code_image"],
        }

    def top_up_existing_esim(self, cli: str, iccid: str, product_id: int) -> str:
        """Пополнение существующей eSIM."""
        if not self.auth_token:
            print("No auth token available for topping up eSIM")
            return None
        response = self._get(
            f"/recharge/?auth_token={self.auth_token}&cli={cli}&iccid={iccid}&product={product_id}"
        )
        print(f"Topped up eSIM with ICCID {iccid} for CLI {cli} and product {product_id}")
        return response.get("message")