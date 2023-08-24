import io
import json
import logging
import re

import http_connection
import product
from lxml import html


class ProductInformation:
    def __init__(self, http_connection: http_connection.HTTPConnection) -> None:
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__http_connection = http_connection
        self.__products = []
        self.init_all_products()

    def __set_all_prices_of_npc(self):
        """
        Ermittelt alle möglichen NPC Preise und setzt diese in den Produkten.
        """

        content = self.__http_connection.get_npc_prices()

        npc_prices_dict = parse_npc_prices_from_html(content)
        # except:
        #    pass #TODO Exception definieren
        # else:
        npc_dict_keys = npc_prices_dict.keys()

        for product in self.__products:
            productname = product.name
            if productname in npc_dict_keys:
                product.price_npc = npc_prices_dict[productname]

    def init_all_products(self):
        """
        Initialisiert alle Produkte.
        """
        content = self.__http_connection.get_all_product_informations()
        re_products = re.search(r"data_products = ({.*}});var", content)
        products = re_products.group(1)
        json_productcs = json.loads(products)
        dict_products = dict(json_productcs)
        keys = dict_products.keys()
        keys = sorted(keys)
        # Nicht genutzte Attribute: img, imgPhase, fileext,
        # clear, edge, pieces, speedup_cooldown in Kategorie z
        for key in keys:
            # 999 ist nur ein Testeintrag und wird nicht benötigt.
            if key == "999":
                continue

            name = dict_products[key]["name"].replace("&nbsp;", " ")
            self.__products.append(
                product.Product(
                    id=int(key),
                    cat=dict_products[key]["category"],
                    sx=dict_products[key]["sx"],
                    sy=dict_products[key]["sy"],
                    name=name,
                    lvl=dict_products[key]["level"],
                    crop=dict_products[key]["crop"],
                    is_plantable=dict_products[key]["plantable"],
                    time=dict_products[key]["time"],
                    price_npc=float("inf"),
                )
            )

        self.__set_all_prices_of_npc()

    def get_product_by_id(self, identifier) -> product.Product:
        for current_product in self.__products:
            if int(identifier) == int(current_product.id):
                return current_product
        return None

    def get_product_by_name(self, name: str) -> product.Product:
        for current_product in self.__products:
            if name.lower() == current_product.name.lower():
                return current_product
        return None

    def get_list_of_all_product_ids(self) -> list:
        product_id_list = []

        for product in self.__products:
            identifier = product.id
            product_id_list.append(identifier)

        return product_id_list


def parse_npc_prices_from_html(html_string: str):
    """
    Parsing all NPC prices from the HTML script of the game help.
    """
    # ElementTree needs a file to parse.
    # With BytesIO a file is created in memory, not on disk.

    html_tree = html.fromstring(html_string)

    table = html_tree.xpath('//body/div[@id="content"]/table')[0]

    dict_result = {}

    for row in table.iter("tr"):
        product_name = row[0].text
        npc_preis = row[1].text

        # Bei der Tabellenüberschrift ist der Text None
        if product_name is not None and npc_preis is not None:
            # NPC-Preis aufbereiten
            npc_preis = str(npc_preis)
            npc_preis = npc_preis.replace(" wT", "")
            npc_preis = npc_preis.replace(".", "")
            npc_preis = npc_preis.replace(",", ".")
            npc_preis = npc_preis.strip()
            if "-" in npc_preis:
                npc_preis = float("inf")
            else:
                npc_preis = float(npc_preis)

            dict_result[product_name] = npc_preis

    return dict_result
