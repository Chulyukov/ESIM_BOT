import re
from io import BytesIO
import httpx  # Асинхронная библиотека для HTTP-запросов
from config import Config
from db.db_bnesim_products import db_insert_bnesim_products


class AsyncBnesimApi:
    def __init__(self):
        self.headers = {"accept": "*/*"}
        self.base_url = "https://api.bnesim.com/v0.1"
        self.auth_token = None

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(headers=self.headers, verify=False) as client:
            try:
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                print(f"Request to {url} failed: {e}")
                return {}

    async def _get(self, path: str, **kwargs) -> dict:
        return await self._request("GET", path, **kwargs)

    async def get_auth_token(self) -> str:
        response = await self._get(
            f"/auth_request/?partner_login={Config.BNESIM_PARTNER_LOGIN}&api_key={Config.BNESIM_API_KEY}&context=admin"
        )
        self.auth_token = response.get("auth_token")
        if not self.auth_token:
            print("Failed to retrieve auth token")
        return self.auth_token

    async def get_products_catalog(self):
        product_list = await self._get("/partners_pricing/?format=json&a=928G")
        main_pattern_1 = r"^Surf (3|5|10|20)+GB in [A-Za-z0-9 ]+ (for|per) 30 days$"
        main_pattern_2 = r"^Surf (3|5|10|20)+GB (for|per) 30 days in [A-Za-z0-9 ]+$"
        main_pattern_3 = r"^Surf (3|5|10|20)+GB/30 days in [A-Za-z0-9 ]+$"
        country_pattern = r" in (.*?) (for|per) "
        new_data = {}
        for product in product_list:
            product_name = product["product_name"]
            if product_name and (
                re.match(main_pattern_1, product_name)
                or re.match(main_pattern_2, product_name)
                or re.match(main_pattern_3, product_name)
            ):
                if re.match(main_pattern_1, product_name):
                    match = re.search(country_pattern, product_name)
                    country = match.group(1).strip().lower()
                elif re.match(main_pattern_2, product_name) or re.match(main_pattern_3, product_name):
                    country = product_name.split(" in ")[-1].lower()
                volume = product["volume"]
                price = float(product["price"])
                product_id = product["id"]

                new_data[product_id] = {
                    "country": country,
                    "volume": volume,
                    "price": price,
                }
        await db_insert_bnesim_products(new_data)
        return new_data

    async def activate_user(self, username):
        if not self.auth_token:
            await self.get_auth_token()
        user = await self._get(f"/license_activation/?auth_token={self.auth_token}&name={username}&plan=254")
        return user.get("cli")

    async def activate_esim(self, cli, product_id):
        if not self.auth_token:
            await self.get_auth_token()
        esim = await self._get(
            f"/sim_card_customer_activation/?auth_token={self.auth_token}&action=activate-esim&cli={cli}&plan={product_id}"
        )
        async with httpx.AsyncClient() as client:
            qr_code_response = await client.get(esim["qr_code_url"])
            qr_code_response.raise_for_status()
            result = {
                "iccid": esim["iccid"],
                "qr_code": BytesIO(qr_code_response.content).read(),
                "qr_code_url": esim["qr_code_url"],
                "ios_universal_installation_link": esim["ios_universal_installation_link"],
            }
        return result

    async def get_iccids_of_user(self, cli):
        if not self.auth_token:
            await self.get_auth_token()
        response = await self._get(
            f"/customer_details/?auth_token={self.auth_token}&cli={cli}&events=5&with_products=0"
        )
        customer_details = response.get("customer_details", {})
        esims_list = customer_details.get("simcards", [])
        iccids_list = [esim.get("iccid") for esim in esims_list]

        result = {
            "length": len(esims_list),
            "iccids": iccids_list,
        }

        return result

    async def get_esim_info(self, iccid):
        if not self.auth_token:
            await self.get_auth_token()
        response = await self._get(
            f"/sim_cards/?auth_token={self.auth_token}&action=get-details&iccid={iccid}&with_products=0"
        )

        if not response:
            print(f"No data available for ICCID {iccid}")
            return {}

        simcard_details = response["simcard_details"]
        result = None  # Инициализируем переменную result по умолчанию

        if simcard_details["data_credit_verbose"] != "":
            country = re.search(
                r"<b>[\d,]+\.\d+ MB</b> in (.+?)(?: valid till \d{2}/\d{2}/\d{4})?<br>",
                simcard_details["data_credit_verbose"],
            ).group(1).strip()

            first_level_key = next(iter(simcard_details["data_credit_details"]))
            second_level_key = next(iter(simcard_details["data_credit_details"][first_level_key]))
            details = simcard_details["data_credit_details"][first_level_key][second_level_key]

            async with httpx.AsyncClient() as client:
                qr_code_response = await client.get(simcard_details["qr_code_image"])
                qr_code_response.raise_for_status()

            result = {
                "ios_link": simcard_details["ios_universal_installation_link"],
                "volume": round(details["associated_product"]["volume"] / 1024, 2),
                "name": f"{round(details['associated_product']['volume'] / 1024, 2)}GB - {country}",
                "country": country,
                "remaining_data": round(details["remaining_mb"] / 1024, 2),
                "qr_code_image": BytesIO(qr_code_response.content).read(),
                "qr_code_url": simcard_details["qr_code_image"],
            }

        return result if result else {}

    async def top_up_existing_esim(self, cli, iccid, product_id):
        if not self.auth_token:
            await self.get_auth_token()
        response = await self._get(
            f"/recharge/?auth_token={self.auth_token}&cli={cli}&iccid={iccid}&product={product_id}"
        )
        print(f"Topped up eSIM with ICCID {iccid} for CLI {cli} and product {product_id}")
        return response.get("message")