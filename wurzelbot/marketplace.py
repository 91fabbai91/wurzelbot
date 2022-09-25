import logging
import re
from . import http_connection


class Marketplace(object):
    def __init__(self, http_connection: http_connection.HTTPConnection) -> None:
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__logger.setLevel(logging.DEBUG)
        self.__http_connection = http_connection
        self.__tradeable_product_ids = None

    def get_all_tradeable_products(self):
        """
        Gibt die IDs aller handelbaren Produkte zurück.
        """
        self.update_all_tradeable_products()
        return self.__tradeable_product_ids
    
    def update_all_tradeable_products(self):
        content = self.__http_connection.get_all_tradeable_products

        tradeableProducts = re.findall(r'markt\.php\?order=p&v=([0-9]{1,3})&filter=1', content)
        for i in range(0, len(tradeableProducts)):
            tradeableProducts[i] = int(tradeableProducts[i])
        self.__tradeable_product_ids = tradeableProducts       
        return tradeableProducts

    def get_all_offers_of_product(self, id):
        """
        Ermittelt alle Angebote eines Produkts.
        """
        self.update_all_tradeable_products()
        
        if self.__tradeable_product_ids != None \
           and \
           id in self.__tradeable_product_ids:

            list_offers = self.__http_connection.get_offers_from_product(id)
        
        else: #Product is not tradeable
            list_offers = None
            
        return list_offers

    def get_cheapest_offer(self, id):
        """
        Ermittelt das günstigste Angebot eines Produkts.
        """

        list_offers = self.get_all_offers_of_product(id)
        
        if len(list_offers) >= 1 \
           and \
           list_offers != None:
            
            return list_offers[0][1]
        
        else: #No Offers
            return None

    def find_big_gap_in_product_offers(self, id, npcPrice):
        """
        Ermittelt eine große Lücke (> 10 %) zwischen den Angeboten und gibt diese zurück.
        """
        
        list_offers = self.get_all_offers_of_product(id)
        list_prices = []

        if (list_offers != None):
            
            #Alle Preise in einer Liste sammeln
            for element in list_offers:
                list_prices.append(element[1])
            
            if (npcPrice != None and id != 0): #id != 0: Coins nicht sortieren
                iList = reversed(range(0, len(list_prices)))
                for i in iList:
                    if list_prices[i] > npcPrice:
                        del list_prices[i]
            
            gaps = []
            #Zum Vergleich werden mindestens zwei Einträge benötigt.
            if (len(list_prices) >= 2):
                for i in range(0, len(list_prices)-1):
                    if (((list_prices[i+1] / 1.1) - list_prices[i]) > 0.0):
                        gaps.append([list_prices[i], list_prices[i+1]])
            
            return gaps