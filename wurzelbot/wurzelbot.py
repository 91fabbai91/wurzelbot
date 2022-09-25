from ast import If
import logging
from . import http_connection
from . import login_data
from . import user
from . import town_park
from . import stock
from . import messenger
from . import quest
from . import product_information


class Wurzelbot(object):

    def __init__(self):
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__logger.setLevel(logging.DEBUG)
        self.__http_connection = http_connection.HTTPConnection()
        self.__messenger = None
        self.__stock = None
        self.__town_park = None
        self.__user = None
        self.__city_quest = None
        self.__product_information = None
        self.__wurzelbot_started = False
        


    def start_wurzelbot(self, login_data: login_data.LoginData):
        self.__logger.debug("Start Wurzelbot")
        self.__http_connection.login(login_data)
        self.__user = user.User(self.__http_connection)
        self.__messenger = messenger.Messenger(self.__http_connection)
        self.__stock = stock.Stock(self.__http_connection)
        self.__town_park = town_park.TownPark(self.__http_connection,1)
        self.__city_quest = quest.CityQuest(self.__http_connection)
        self.__product_information = product_information.ProductInformation(self.__http_connection)
        self.__wurzelbot_started = True
        self.__logger.debug("Wurzelbot started!")


    def stop_wurzelbot(self):
        self.__logger.debug("Stop Wurzelbot")
        self.__http_connection.logout()
        self.__wurzelbot_started = False


    def water_plants_in_all_gardens(self):
        """
        Alle Gärten des Spielers werden komplett bewässert.
        """
        if not self.__wurzelbot_started:
            raise NotStartedException("Wurzelbot not started yet")
        for garden in self.__user.gardens:
            garden.water_plants()

    def get_empty_fields_of_gardens(self):
        if not self.__wurzelbot_started:
            raise NotStartedException("Wurzelbot not started yet")
        
        empty_fields = []
        try:
            for garden in self.__user.gardens:
                empty_fields.append(garden.get_empty_fields())
        except:
            self.__logger.error('Konnte leere Felder von Garten ' + str(garden.id) + ' nicht ermitteln.')
        else:
            pass
        return empty_fields

    def has_empty_fields(self):
        if not self.__wurzelbot_started:
            raise NotStartedException("Wurzelbot not started yet")

        empty_fields = self.get_empty_fields_of_gardens()
        amount = 0
        for garden in empty_fields:
            amount += len(garden)

        return amount > 0

    def get_weed_fields_of_gardens(self):
        """
        Gibt alle Unkrau-Felder aller normalen Gärten zurück.
        """
        if not self.__wurzelbot_started:
            raise NotStartedException("Wurzelbot not started yet")
        weed_fields = []
        try:
            for garden in self.__user.gardens:
                weed_fields.append(garden.get_weed_fields())
        except:
            self.__logBot.error('Konnte Unkraut-Felder von Garten ' + str(garden.id) + ' nicht ermitteln.')
        else:
            pass

        return weed_fields

    def harvest_all_garden(self):
        if not self.__wurzelbot_started:
            raise NotStartedException("Wurzelbot not started yet")
        #TODO: Wassergarten ergänzen
        try:
            for garden in self.__user.gardens:
                garden.harvest()
                
            if self.__user.is_aqua_garden_available():
                pass#self.waterPlantsInAquaGarden()

            self.__stock.update_number_in_stock()
        except:
            self.__logger.error('Konnte nicht alle Gärten ernten.')
        else:
            self.__logger.info('Konnte alle Gärten ernten.')
            pass

    def collectCashFromPark(self):
        if not self.__wurzelbot_started:
            raise NotStartedException("Wurzelbot not started yet")
        self.__town_park.collect_cash_points_from_park()

    def print_stock(self):
        if not self.__wurzelbot_started:
            raise NotStartedException("Wurzelbot not started yet")
        isSmthPrinted = False
        for product_id in self.__stock.get_keys():
            product = self.__product_information.get_product_by_id(product_id)
            
            amount = self.__stock.get_stock_by_product_id(product_id)
            if amount == 0: continue
            
            print(str(product.getName()).ljust(30) + 'Amount: ' + str(amount).rjust(5))
            isSmthPrinted = True
    
        if not isSmthPrinted:
            print('Your stock is empty')


    def getLowestStockEntry(self):
        if not self.__wurzelbot_started:
            raise NotStartedException("Wurzelbot not started yet")
        entryID = self.__stock.get_lowest_stock_entry()
        if entryID == -1: return 'Your stock is empty'
        return self.__product_information.get_product_by_id(entryID).getName()

    def get_ordered_stock_list(self):
        if not self.__wurzelbot_started:
            raise NotStartedException("Wurzelbot not started yet")
        orderedList = ''
        for product_id in self.__stock.get_ordered_stock_list():
            orderedList += str(self.__product_information.get_product_by_id(product_id).getName()).ljust(20)
            orderedList += str(self.__stock.get_ordered_stock_list()[product_id]).rjust(5)
            orderedList += str('\n')
        return orderedList.strip()

    def get_lowest_plant_stock_entry(self):
        if not self.__wurzelbot_started:
            raise NotStartedException("Wurzelbot not started yet")
        lowest_stock = -1
        lowest_product_id = -1
        for product_id in self.__stock.get_ordered_stock_list():
            if not self.__product_information.get_product_by_id(product_id).is_plant or \
                not self.__product_information.get_product_by_id(product_id).is_plantable:
                continue

            current_stock = self.__stock.get_stock_by_product_id(product_id)
            if lowest_stock == -1 or current_stock < lowest_stock:
                lowest_stock = current_stock
                lowest_product_id = product_id
                continue

        if lowest_product_id == -1: return 'Your stock is empty'
        return self.__product_information.get_product_by_id(lowest_product_id).getName()

    def renewAllItemsInPark(self):
        if not self.__wurzelbot_started:
            raise NotStartedException("Wurzelbot not started yet")
        return self.__town_park.renew_items_in_park()

    def grow_plants_in_gardens(self, productName, amount=-1):
        """
        Pflanzt so viele Pflanzen von einer Sorte wie möglich über alle Gärten hinweg an.
        """
        if not self.__wurzelbot_started:
            raise NotStartedException("Wurzelbot not started yet")
        planted = 0

        product = self.__product_information.get_product_by_name(productName)

        if product is None:
            logMsg = 'Pflanze "' + productName + '" nicht gefunden'
            self.__logger.error(logMsg)
            print(logMsg)
            return -1

        if not product.isPlant() or not product.isPlantable():
            logMsg = '"' + productName + '" kann nicht angepflanzt werden'
            self.__logger.error(logMsg)
            print(logMsg)
            return -1

        for garden in self.__user.gardens:
            if amount == -1 or amount > self.__stock.get_stock_by_product_id(product.getID()):
                amount = self.__stock.get_stock_by_product_id(product.getID())
            planted += garden.grow_plants(product.getID(), product.getSX(), product.getSY(), amount)
        
        self.__stock.update_number_in_stock()

        return planted

    def get_plants_in_garden(self):
        for garden in self.__user.gardens:
            garden.update_planted_fields()

class NotStartedException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

