import logging
import re

import http_connection


class Marketplace(object):
    FEE_PERCENTAGE = 0.1
    MINIMAL_DISCOUNT = 0.01

    def __init__(self, http_connection: http_connection.HTTPConnection) -> None:
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__http_connection = http_connection
        self.__tradeable_product_ids = None

    def get_all_tradeable_products(self):
        """
        Returns the IDs of all tradable products.
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

    def get_all_offers_of_product(self, identifier):
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
            list_offers = None

        return list_offers

    def get_cheapest_offer(self, identifier):
        """
        Determines the most favorable offer of a product.
        """

        list_offers = self.get_all_offers_of_product(identifier)

        if list_offers is not None and len(list_offers) >= 1:
            return list_offers[0][1]
        return None

    def sell_on_market(self, item_id: int, price: float, number: int):
        self.__http_connection.sell_on_market(item_id, price, number)

    def find_big_gap_in_product_offers(self, identifier, npc_price):
        """
        Identifies a large gap (> 10%) between offers and returns it.
        """

        list_offers = self.get_all_offers_of_product(identifier)
        list_prices = []

        if list_offers is not None:
            # Collect all prices in one list
            for element in list_offers:
                list_prices.append(element[1])

            if npc_price is not None and identifier != 0:  # id != 0: Do not sort coins
                reversed_list = reversed(range(0, len(list_prices)))
                for i in reversed_list:
                    if list_prices[i] > npc_price:
                        del list_prices[i]

            gaps = []
            # At least two entries are required for comparison.
            if len(list_prices) >= 2:
                for i in range(0, len(list_prices) - 1):
                    if ((list_prices[i + 1] / 1.1) - list_prices[i]) > 0.0:
                        gaps.append([list_prices[i], list_prices[i + 1]])

            return gaps
