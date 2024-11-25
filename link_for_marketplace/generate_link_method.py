import uuid

from link_for_marketplace.db_link import db_insert_esims


def generate_links(esim_number, country, gb_amount):
    esim_list = [{"id": str(uuid.uuid4()), "country": country, "gb_amount": gb_amount} for _ in range(esim_number)]
    db_insert_esims(esim_list)


generate_links(1, "turkey", 3)
