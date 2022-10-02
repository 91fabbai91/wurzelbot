import json
import logging
import re
from bidict import bidict
import http_connection

class Stock(object):
    def __init__(self, http_connection: http_connection.HTTPConnection):
        self.__http_connection = http_connection
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__product_information = None
        self.__products = {}
        self.get_product_information_from_server()
        self.init_product_list(self.__product_information)
        self.update_number_in_stock()
    

    def get_product_information_from_server(self):
        content = self.__http_connection.get_all_product_informations()

        reProducts = re.search(r'data_products = ({.*}});var', content)
        self.__product_information = json.loads(reProducts.group(1))
        return self.__product_information

    def __reset_numbers_in_stock(self):
        for productID in self.__products.keys():
            self.__products[productID] = 0


    def init_product_list(self, productList):
        
        for productID in productList:
            self.__products[str(productID)] = 0

    def update_number_in_stock(self):
        """
        Führt ein Update des Lagerbestands für alle Produkte durch.
        """
        
        self.__reset_numbers_in_stock()
            
        inventory = self.__http_connection.read_storage_from_server()
        
        for i in inventory:
            self.__products[i] = inventory[i]

    def get_keys(self):
        return self.__products.keys()
        
    def get_stock_by_product_id(self, productID):
        return self.__products[str(productID)]

    

    def get_ordered_stock_list(self):
        sorted_stock = dict(sorted(self.__products.items(), key=lambda item: item[1]))
        filtered_stock = dict()
        for productID in sorted_stock:
            if sorted_stock[str(productID)] == 0: continue
            filtered_stock[str(productID)] = sorted_stock[str(productID)]
        
        return filtered_stock

    def get_lowest_stock_entry(self):
        for productID in self.get_ordered_stock_list().keys():
            return productID
        return -1