import re
import logging
import json
from . import http_connection
from . import product


class ProductInformation(object):

    def __init__(self, http_connection: http_connection.HTTPConnection) -> None:
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__http_connection = http_connection
        self.__products = []
        self.init_all_products()

    def __set_all_prices_of_npc(self):
        """
        Ermittelt alle möglichen NPC Preise und setzt diese in den Produkten.
        """
        
        dNPC = self.__http_connection.get_npc_prices()
        dNPCKeys = dNPC.keys()
        
        for product in self.__products:
            productname = product.name
            if productname in dNPCKeys:
                product.price_npc = dNPC[productname]

    def init_all_products(self):
        """
        Initialisiert alle Produkte.
        """
        content = self.__http_connection.get_all_product_informations()
        reProducts = re.search(r'data_products = ({.*}});var', content)
        products = reProducts.group(1)
        jProducts = json.loads(products)
        dictProducts = dict(jProducts)
        keys = dictProducts.keys()
        keys = sorted(keys)
        # Nicht genutzte Attribute: img, imgPhase, fileext, clear, edge, pieces, speedup_cooldown in Kategorie z
        for key in keys:
                # 999 ist nur ein Testeintrag und wird nicht benötigt.
            if key == '999':
                continue

            name = dictProducts[key]['name'].replace('&nbsp;', ' ')
            self.__products.append(product.Product(id        = int(key), \
                                            cat       = dictProducts[key]['category'], \
                                            sx        = dictProducts[key]['sx'], \
                                            sy        = dictProducts[key]['sy'], \
                                            name      = name.encode('utf-8'), \
                                            lvl       = dictProducts[key]['level'], \
                                            crop      = dictProducts[key]['crop'], \
                                            plantable = dictProducts[key]['plantable'], \
                                               time      = dictProducts[key]['time']))
                
        self.__set_all_prices_of_npc()

    def get_product_by_id(self, id) -> product.Product:
        for product in self.__products:
            if int(id) == int(product.id): return product
            
    def get_product_by_name(self, name : str) -> product.Product:
        for product in self.__products:
            if (name.lower() in product.name.lower()): return product
        return None

    def get_list_of_all_product_ids(self) -> list:
        
        product_id_list = []
        
        for product in self.__products:
            id = product.id
            product_id_list.append(id)
            
        return product_id_list