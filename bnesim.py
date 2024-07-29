import re
import logging
import time
from io import BytesIO
import requests

from config import Config
from db.db_bnesim import db_insert_bnesim_products

logger = logging.getLogger('BnesimApiLogger')
logger.setLevel(logging.WARNING)
file_handler = logging.FileHandler('logs/bnesim_api.log')
file_handler.setLevel(logging.WARNING)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class BnesimApi:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {"accept": "*/*"}
        self.base_url = "https://api.bnesim.com/v0.1"
        self.auth_token = self.get_auth_token()

    def _request(self, method: str, path: str, **kwargs) -> dict:
        url = f"{self.base_url}/{path}"
        try:
            response = self.session.request(method, url, verify=False, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.warning(f"Request to {url} failed: {e}")
            return {}

    def _get(self, path: str, **kwargs) -> dict:
        return self._request("GET", path, **kwargs)

    def get_auth_token(self) -> str:
        response =  self._get(
            f"/auth_request/?partner_login={Config.BNESIM_PARTNER_LOGIN}&api_key={Config.BNESIM_API_KEY}&context=admin")
        auth_token = response.get("auth_token")
        if not auth_token:
            logging.warning("Failed to retrieve auth token")
        return auth_token

    def get_products_catalog(self):
        product_list =  self._get("/partners_pricing/?format=json&a=928G")
        pattern = r'^Surf (1|3|5|10|20)+GB in [A-Za-z0-9 ]+$'
        for product in product_list:
            product_name = product.get("product_name")
            if product_name and re.match(pattern, product_name) and \
                    any(product_name.endswith(country) for country in
                        ["Egypt", "Turkey", "United Arabian Emirates", "Thailand", "Georgia"]):
                logging.info(f"{product.get('id')} - {product_name} - {product.get('price')}")
                db_insert_bnesim_products(product.get("id"), product_name.split(" ")[-1], product.get("volume"))

    def activate_user(self, username):
        if not self.auth_token:
            logging.warning("No auth token available for activating user")
            return None
        user = self._get(f"/license_activation/?auth_token={self.auth_token}&name={username}&plan=254")
        return user.get("cli")

    def activate_esim(self, cli, product_id):
        if not self.auth_token:
            logging.warning("No auth token available for activating user")
            return None
        esim =  self._get("/sim_card_customer_activation/?"
                               f"auth_token={self.auth_token}&action=activate-esim&cli={cli}&plan={product_id}")
        return BytesIO(requests.get(esim["qr_code_url"]).content).read()

    def get_iccids_of_user(self, cli):
        if not self.auth_token:
            logging.warning("No auth token available for getting ICCIDs")
            return {}
        response =  self._get(
            f"/customer_details/?auth_token={self.auth_token}&cli={cli}&events=5&with_products=0")
        customer_details = response.get("customer_details", {})
        esims_list = customer_details.get("simcards", [])
        iccids_list = [esim.get("iccid") for esim in esims_list]

        result = {
            "length": len(esims_list),
            "iccids": iccids_list
        }

        logging.info(f"Number of eSIMs: {result['length']}")

        return result

    def get_esim_info(self, iccid):
        if not self.auth_token:
            logging.warning("No auth token available for getting eSIM info")
            return {}
        response = self._get(
            f"/sim_cards/?auth_token={self.auth_token}&action=get-details&iccid={iccid}&with_products=0")

        if not response:
            logging.warning(f"No data available for ICCID {iccid}")
            return {}

        simcard_details = response["simcard_details"]
        country = simcard_details["data_credit_verbose"].split(" ")[-1].replace("<br>", "")
        no_expiration = simcard_details["data_credit_details"][country]["no expiration"]

        result = {
            "volume": round(no_expiration["associated_product"]["volume"] / 1024, 2),
            "name": f"{round(no_expiration['associated_product']['volume'] / 1024, 2)}GB - {country}",
            "country": country,
            "remaining_data": round(no_expiration["remaining_mb"] / 1024, 2),
            "qr_code_image": BytesIO(requests.get(simcard_details["qr_code_image"]).content).read()
        }

        logging.info(f"eSIM info for ICCID {iccid}: {result}")
        return result

    def top_up_existing_esim(self, cli, iccid, product_id):
        if not self.auth_token:
            logging.warning("No auth token available for topping up eSIM")
            return
        response = self._get(
            f"/recharge/?auth_token={self.auth_token}&cli={cli}&iccid={iccid}&product={product_id}")
        logging.info(f"Topped up eSIM with ICCID {iccid} for CLI {cli} and product {product_id}")
        return response["message"]
