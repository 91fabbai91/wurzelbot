from ast import If
from itertools import product
import logging
from collections import Counter
from . import http_connection
from . import login_data
from . import user
from . import town_park
from . import stock
from . import messenger
from . import quest
from . import product_information
from . import marketplace
from . import bees_farm

class Wurzelbot(object):

    def __init__(self):
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__http_connection = http_connection.HTTPConnection()
        self.__messenger = None
        self.__stock = None
        self.__town_park = None
        self.__user = None
        self.__city_quest = None
        self.__park_quest = None
        self.__deco_garden_quest = None
        self.__product_information = None
        self.__marketplace = None
        self.__bees_farm = None
        self.__wurzelbot_started = False

        


    def start_wurzelbot(self, login_data: login_data.LoginData):
        self.__logger.debug("Start Wurzelbot")
        self.__http_connection.login(login_data)
        self.__user = user.User(self.__http_connection)
        self.__messenger = messenger.Messenger(self.__http_connection)
        self.__stock = stock.Stock(self.__http_connection)
        if self.__user.is_town_park_available():
            self.__town_park = town_park.TownPark(self.__http_connection,1)
        self.__city_quest = quest.CityQuest(self.__http_connection)
        self.__deco_garden_quest = quest.DecoGardenQuest(self.__http_connection)
        self.__park_quest = quest.ParkQuest(self.__http_connection)
        self.__product_information = product_information.ProductInformation(self.__http_connection)
        self.__marketplace = marketplace.Marketplace(self.__http_connection)
        if self.__user.is_honey_farm_available():
            self.__bees_farm = bees_farm.BeesFarm(self.__http_connection)
        self.__wurzelbot_started = True
        self.__logger.debug("Wurzelbot started!")


    def stop_wurzelbot(self):
        self.__logger.debug("Stop Wurzelbot")
        self.__http_connection.logout()
        self.__wurzelbot_started = False

    def start_all_bees_tour(self):
        if self.__user.is_honey_farm_available():
            self.__bees_farm.start_all_bees_tour(bees_farm.BeesTour.TWO_HOURS_TOUR)


    def sell_on_market(self, item_id: int , price: float, number: int):
        self.__marketplace.sell_on_market(item_id, price, number)

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

    def destroy_weed_field(self, field_id):
        self.__http_connection.destroy_weed_field(field_id)


    def harvest_all_garden(self):
        if not self.__wurzelbot_started:
            raise NotStartedException("Wurzelbot not started yet")
        #TODO: Wassergarten ergänzen
        try:
            for garden in self.__user.gardens:
                garden.harvest()

            self.__stock.update_number_in_stock()
        except:
            self.__logger.error('Konnte nicht alle Gärten ernten.')
        else:
            self.__logger.info('Konnte alle Gärten ernten.')

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

    def renew_all_items_in_park(self):
        if not self.__wurzelbot_started:
            raise NotStartedException("Wurzelbot not started yet")
        if not self.__user.is_town_park_available():
            self.__town_park.renew_all_items_in_park()

    def grow_plants_in_gardens_by_name(self, productName, amount=-1):
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

        if not product.is_plant or not product.is_plantable:
            logMsg = '"' + productName + '" kann nicht angepflanzt werden'
            self.__logger.error(logMsg)
            print(logMsg)
            return -1

        for garden in self.__user.gardens:
            if amount == -1 or amount > self.__stock.get_stock_by_product_id(product.id):
                amount = self.__stock.get_stock_by_product_id(product.id)
            planted += garden.grow_plants(product.id, product.sx, product.sy, amount)
        
        self.__stock.update_number_in_stock()

        return planted

    
    
    def grow_anything(self):
        for product_id, amount in self.__stock.get_ordered_stock_list().items():
            product = self.__product_information.get_product_by_id(product_id)
            if self.grow_plants_in_gardens_by_name(product.name, amount) == 0 and product.sx == 1 and product.sy == 1:
                return
            

    def get_plants_in_garden(self):
        gardens = []
        for garden in self.__user.gardens:
            garden.update_planted_fields()
            gardens.append(garden.fields)
        return gardens

    def number_of_plants_in_garden(self):
        plant_count = Counter()
        for garden in self.get_plants_in_garden():
            plant_count =  plant_count + Counter(r[1] for r in garden)
        return dict(plant_count)
    
    def get_missing_quest_amount(self, quest: quest.Quest) -> dict:
        missing_quest_amount = {}
        amounts, _  = quest.get_quest()
        number_of_plants = self.number_of_plants_in_garden()
        for name, value in amounts.items():
            if name[-1] == 'n':
                name = name.rstrip(name[-1])
            product = self.__product_information.get_product_by_name(name)
            stock = self.__stock.get_stock_by_product_id(product.id)
            try:
                stock = stock + product.crop * number_of_plants[product.id]
            except KeyError:
                self.__logger.debug("No product of id {id} planted".format(id=product.id))
            self.__logger.debug(" missing amount: {amount} {product}".format(amount=value-stock, product=product.name))
            if value-stock > 0:
                missing_quest_amount.update({product.name: value-stock})
        return missing_quest_amount

    def plant_according_to_quest(self, quest_type_name: str):
        if quest_type_name == quest.CityQuest.__name__:
            quest_level = self.__city_quest
        elif quest_type_name == quest.ParkQuest.__name__:
            quest_level = self.__park_quest
        elif quest_type_name == quest.DecoGardenQuest.__name__:
            quest_level = self.__deco_garden_quest
        else:
            raise NameError("No Element named {}".format(quest_type_name))
        missing_amount = self.get_missing_quest_amount(quest=quest_level)
        for product_name, amount in missing_amount.items():
            self.grow_plants_in_gardens_by_name(product_name, amount)
    



class NotStartedException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

