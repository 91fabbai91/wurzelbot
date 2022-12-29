import json
import logging
import re
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
        Performs an update of the stock for all products.
        """
        
        self.__reset_numbers_in_stock()
            
        inventory = self.__http_connection.read_storage_from_server()
        
        for i in inventory:
            self.__products[i] = inventory[i]

    def get_keys(self):
        return self.__products.keys()
        
    def get_stock_by_product_id(self, productID):
        return self.__products[str(productID)]

    

    def get_ordered_stock_list(self,order_attribute:str):
        extended_product_list = merge_dictionaries(self.__product_information,self.__products)
        sorted_stock = dict(sorted(extended_product_list.items(), key=lambda item: item[1][order_attribute]))
        sorted_stock = dict(filter(lambda x: x[1]['amount'] != 0, sorted_stock.items()))
        
        return sorted_stock

    def get_lowest_stock_entry(self):
        for productID in self.get_ordered_stock_list('amount').keys():
            return productID
        return -1


def merge_dictionaries(dictionary1: dict,dictionary2:dict) -> dict:
    dictionary3 = {**dictionary1, **dictionary2}
    for key, value in dictionary3.items():
        if key in dictionary1 and key in dictionary2:
               dictionary3[key] = {'amount':value , **dictionary1[key]}
    return dictionary3    