import logging
import re

import http_connection


class Marketplace:
    FEE_PERCENTAGE = 0.1
    MINIMAL_DISCOUNT = 0.01

    def __init__(self, http_connection: http_connection.HTTPConnection) -> None:
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__http_connection = http_connection
        self.__tradeable_product_ids = None

    def get_all_tradeable_products(self):
        """
        Returns the IDs of all tradeable products.
        """
        self.update_all_tradeable_products()
        return self.__tradeable_product_ids

    def update_all_tradeable_products(self):
        content = self.__http_connection.get_all_tradeable_products().decode()
        tradeable_products = re.findall(
            r"markt\.php\?order=p&v=([0-9]{1,3})&filter=1", content
        )

        tradeable_products = [int(x) for x in tradeable_products]
        self.__tradeable_product_ids = tradeable_products
        return tradeable_products

    def get_all_offers_of_product(self, identifier: int) -> list:
        """
        Determines all offers of a product.
        """
        self.update_all_tradeable_products()

        if (
            self.__tradeable_product_ids is not None
            and identifier in self.__tradeable_product_ids
        ):
            list_offers = self.__http_connection.get_offers_from_product(identifier)

        else:  # Product is not tradeable
            list_offers = []

        return list_offers

    def get_cheapest_offer(self, identifier: int, filtered_username: str = "") -> float:
        """
        Determines the most favorable offer of a product.
        """

        list_offers = self.get_all_offers_of_product(identifier)
        if list_offers is not None:
            list_offers = list(
                filter(lambda x: x.seller == filtered_username, list_offers)
            )
            if len(list_offers) > 0:
                return list_offers[0].price
        return None

    def sell_on_market(self, item_id: int, price: float, number: int):
        self.__http_connection.sell_on_market(item_id, price, number)
