import time
import httpx
from config import Config
from db.db_queries import db_insert_monty_countries, db_get_iso3_code


class SingletonMeta(type):
    """Метакласс для реализации Singleton."""
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class MontyApiAsync(metaclass=SingletonMeta):
    def __init__(self):
        self.base_url = "https://resellerapi.montyesim.com/api/v0"
        self.headers = {
            "accept": "*/*",
            "Content-Type": "application/json",
        }
        self.access_token = None
        self.token_expiry = 0  # Время истечения токена в формате UNIX

    async def _refresh_token_if_needed(self):
        """Проверяет, истёк ли токен, и обновляет его при необходимости."""
        current_time = time.time()
        if not self.access_token or current_time >= self.token_expiry:
            await self._update_access_token()

    async def _update_access_token(self):
        """Обновляет токен и сохраняет время его истечения."""
        self.access_token = await self._get_auth_token_directly()  # Используем прямой запрос
        self.headers["Access-Token"] = self.access_token
        self.token_expiry = time.time() + 60 * 9  # Токен действует 9 минут

    async def _get_auth_token_directly(self) -> str:
        """Получает токен авторизации напрямую, без использования _request."""
        body = {
            "username": Config.MONTY_LOGIN,
            "password": Config.MONTY_PASSWORD
        }
        url = f"{self.base_url}/Agent/login"
        async with httpx.AsyncClient(verify=False) as client:
            try:
                response = await client.post(url, json=body, headers=self.headers)
                response.raise_for_status()
                return response.json().get("access_token", "")
            except httpx.RequestError as e:
                print(f"Request to {url} failed: {e}")
                return ""

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        """Асинхронный запрос к API с проверкой токена."""
        await self._refresh_token_if_needed()  # Проверяем и обновляем токен, если нужно
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(verify=False) as client:
            try:
                response = await client.request(method, url, headers=self.headers, **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                print(f"Request to {url} failed: {e}")
                return {}

    async def _get(self, path: str, **kwargs) -> dict:
        return await self._request("GET", path, **kwargs)

    async def _post(self, path: str, **kwargs) -> dict:
        return await self._request("POST", path, **kwargs)

    async def enrich_iso3_codes(self):
        """Обогащает базы данных кодами ISO3."""
        iso3_codes = await self._get(f"/AvailableCountries?reseller_admin_view=true")
        countries = [
            "turkey", "thailand", "egypt", "united arab emirates", "italy",
            "greece", "spain", "cyprus", "france", "montenegro",
            "maldives", "vietnam", "india", "china", "morocco",
            "indonesia", "czech republic", "georgia", "japan", "sri lanka"
        ]

        for country in countries:
            for iso3_code in iso3_codes.get("countries", []):
                if iso3_code["country_name"] == country.title():
                    db_insert_monty_countries(country, iso3_code["iso3_code"])

    async def get_bundle_data(self, country: str):
        """Получает данные пакета для указанной страны."""
        iso3_code = db_get_iso3_code(country)
        response = await self._get(
            f"/Bundles?country_code={iso3_code}&page_size=100&page_number=1&sort_by=price_asc&reseller_admin_view=true"
        )
        return response.get("bundles", [])

    async def activate_esim(self, bundle_code: str, uuid: str):
        """Активирует eSIM по коду пакета и UUID."""
        body = {
            "bundle_code": bundle_code,
            "whatsapp_number": "+79774879583",
            "email": "esim.unity@mail.ru",
            "name": "Admin",
            "order_reference": uuid
        }
        await self._post("/Bundles", json=body)

    async def get_esim_info(self, uuid: str):
        """Получает информацию о eSIM по UUID."""
        response = await self._get(f"/Orders?order_reference={uuid}")
        return response.get("orders", [])[0]

    async def get_remaining_data(self, order_id: str):
        """Получает остаток данных по ID заказа."""
        response = await self._get(f"/Orders/Consumption?order_id={order_id}")
        return response.get("data_remaining", None)