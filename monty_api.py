
import requests

from config import Config
from db.db_queries import db_insert_monty_countries, db_get_iso3_code


class MontyApi:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://resellerapi.montyesim.com/api/v0"
        self.headers = {
            "accept": "*/*",
            "Content-Type": "application/json",
        }
        self._update_access_token()

    def _update_access_token(self):
        self.headers["Access-Token"] = self.get_auth_token()

    def _request(self, method: str, path: str, **kwargs) -> dict:
        url = f"{self.base_url}{path}"
        try:
            response = self.session.request(method, url, verify=False, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Request to {url} failed: {e}")
            return {}

    def _get(self, path: str, **kwargs) -> dict:
        return self._request("GET", path, **kwargs)

    def _post(self, path: str, **kwargs) -> dict:
        return self._request("POST", path, **kwargs)

    def get_auth_token(self) -> str:
        body = {
            "username": Config.MONTY_LOGIN,
            "password": Config.MONTY_PASSWORD
        }
        response = self._post("/Agent/login", json=body)
        auth_token = response["access_token"]
        return auth_token

    def enrich_iso3_codes(self):
        iso3_codes = self._get(f"/AvailableCountries?reseller_admin_view=true")

        countries =[
            "turkey", "thailand", "egypt", "united arab emirates", "italy",
            "greece", "spain", "cyprus", "france", "montenegro",
            "maldives", "vietnam", "india", "china", "morocco",
            "indonesia", "czech republic", "georgia", "japan", "sri lanka"
        ]

        for country in countries:
            for iso3_code in iso3_codes["countries"]:
                if iso3_code["country_name"] == country.title():
                    db_insert_monty_countries(country, iso3_code["iso3_code"])

    def get_bundle_data(self, country: str):
        necessary_bundles = []

        iso3_code = db_get_iso3_code(country)

        return self._get(f"/Bundles?country_code={iso3_code}&page_size=100&page_number=1&sort_by=price_asc&reseller_admin_view=true")["bundles"]

    def activate_esim(self, bundle_code: str, uuid: str):
        body = {
            "bundle_code": bundle_code,
            "whatsapp_number": "+79774879583",
            "email": "esim.unity@mail.ru",
            "name": "ADmin",
            "order_reference": uuid
        }
        self._post("/Bundles", json=body)

    def get_esim_info(self, uuid: str):
        response = self._get(f"/Orders?order_reference={uuid}")
        return response["orders"][0]

    def get_remaining_data(self, order_id: str):
        response = self._get(f"/Orders/Consumption?order_id={order_id}")
        return response["data_remaining"]


# monty = MontyApi()
# monty.enrich_iso3_codes()
# result = monty.get_necessary_bundle_code("japan", "20")
# monty.activate_esim("TUR_0405202408472420", "Z2JWrhoCNXSrMbUntVH6UZW")
# result = monty.get_esim_info("Z2JWrhoCNXSrMbUntVH6UZW")
# print(result)
# print(f"\nLength:{len(result)}")
