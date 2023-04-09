from ast import If
from itertools import product
import logging
from collections import Counter
from pydantic import SecretStr
import http_connection
import login_data
import user
import town_park
import stock
import messenger
import quest
import product_information
import marketplace
import bees_farm
import notes
import wimp
import garden

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
        self.__bee_farm_quest = None
        self.__tree_quest = None
        self.__product_information = None
        self.__marketplace = None
        self.__bees_farm = None
        self.__notes = None
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
        self.__bee_farm_quest = quest.BeesGardenQuest(self.__http_connection)
        self.__tree_quest= quest.TreeQuest(self.__http_connection)
        self.__product_information = product_information.ProductInformation(self.__http_connection)
        self.__marketplace = marketplace.Marketplace(self.__http_connection)
        if self.__user.is_honey_farm_available():
            self.__bees_farm = bees_farm.BeesFarm(self.__http_connection)
        self.__notes = notes.Notes(self.__http_connection)
        self.__wurzelbot_started = True
        self.__logger.debug("Wurzelbot started!")


    def stop_wurzelbot(self):
        self.__logger.debug("Stop Wurzelbot")
        self.__http_connection.logout()
        self.__wurzelbot_started = False

    def start_all_bees_tour(self):
        if self.__user.is_honey_farm_available():
            self.__bees_farm.start_all_bees_tour(bees_farm.BeesTour.TWO_HOURS_TOUR)


    def sell_on_market(self, name: str , price: float, number: int):
        self.__marketplace.sell_on_market(self.__product_information.get_product_by_name(name).id, price, number)

    def get_daily_login_bonus(self):
        self.__user.get_daily_login_bonus()

    def water_plants_in_all_gardens(self):
        """
        All the gardens of the player are completely irrigated.
        """
        if not self.__wurzelbot_started:
            raise NotStartedException("Wurzelbot not started yet")
        for garden in self.__user.gardens:
            garden.water_plants()


    def get_empty_fields_of_gardens(self) -> list:
        if not self.__wurzelbot_started:
            raise NotStartedException("Wurzelbot not started yet")
        
        empty_fields = []
        try:
            for garden in self.__user.gardens:
                empty_fields.append(garden.get_empty_fields())
        except:
            self.__logger.error(f'Could not determine empty field from garden {garden.id}')
        else:
            pass
        return empty_fields

    def has_empty_fields(self) -> bool:
        if not self.__wurzelbot_started:
            raise NotStartedException("Wurzelbot not started yet")

        empty_fields = self.get_empty_fields_of_gardens()
        amount = 0
        for garden in empty_fields:
            amount += len(garden)

        return amount > 0

    def get_weed_fields_of_gardens(self) -> list:
        """
        Returns all weed fields of all normal gardens.
        """
        if not self.__wurzelbot_started:
            raise NotStartedException("Wurzelbot not started yet")
        weed_fields = []
        try:
            for garden in self.__user.gardens:
                weed_fields.append(garden.get_weed_fields())
        except:
            self.__logBot.error(f'Could not determine weed fields of garden {garden.id}')
        else:
            pass

        return weed_fields

    def destroy_weed_field(self, field_id):
        self.__http_connection.destroy_weed_field(field_id)


    def harvest_all_garden(self):
        if not self.__wurzelbot_started:
            raise NotStartedException("Wurzelbot not started yet")
        try:
            for garden in self.__user.gardens:
                garden.harvest()

            self.__stock.update_number_in_stock()
        except:
            self.__logger.error('Could not harvest all the gardens.')
        else:
            self.__logger.info('Was able to harvest all the gardens.')

    def collect_cash_from_park(self):
        if not self.__wurzelbot_started:
            raise NotStartedException("Wurzelbot not started yet")
        if self.__user.is_town_park_available():
            self.__town_park.collect_cash_points_from_park()

    def print_stock(self):
        if not self.__wurzelbot_started:
            raise NotStartedException("Wurzelbot not started yet")
        isSmthPrinted = False
        for product_id in self.__stock.get_keys():
            product = self.__product_information.get_product_by_id(product_id)
            
            amount = self.__stock.get_stock_by_product_id(product_id)
            if amount == 0: continue
            
            self.__logger.info(f'{product.getName().ljust(30)} Amount: {amount.rjust(5)}')
            isSmthPrinted = True
    
        if not isSmthPrinted:
            self.__logger.info('Your stock is empty')

    def get_ordered_stock_list(self) -> list:
        if not self.__wurzelbot_started:
            raise NotStartedException("Wurzelbot not started yet")
        orderedList = ''
        for product_id in self.__stock.get_ordered_stock_list('amount')[0]:
            orderedList += str(self.__product_information.get_product_by_id(product_id).getName()).ljust(20)
            orderedList += str(self.__stock.get_ordered_stock_list('amount')[1][product_id]).rjust(5)
            orderedList += str('\n')
        return orderedList.strip()

    def get_lowest_plant_stock_entry(self) -> str:
        if not self.__wurzelbot_started:
            raise NotStartedException("Wurzelbot not started yet")
        lowest_stock = -1
        lowest_product_id = -1
        for product_id in self.__stock.get_ordered_stock_list('amount')[0]:
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
        if self.__user.town_park_available:
            self.__town_park.renew_all_items_in_park()

    def grow_plants_in_gardens_by_name(self, productName, amount=-1) -> int:
        """
        Plant as many plants of one variety as possible across all gardens.
        """
        if not self.__wurzelbot_started:
            raise NotStartedException("Wurzelbot not started yet")
        planted_totally = 0

        product = self.__product_information.get_product_by_name(productName)

        if product is None:
            logMsg = f'plant {productName} not found'
            self.__logger.error(logMsg)
            return 0

        if not product.is_plantable or not product.is_plant():
            logMsg = f'{productName} could not get planted'
            self.__logger.error(logMsg)
            return 0

        for garden in self.__user.gardens:
            if amount == -1 or amount > self.__stock.get_stock_by_product_id(product.id):
                amount = self.__stock.get_stock_by_product_id(product.id)
            planted = garden.grow_plants(product, product.sx, product.sy, amount)
            planted_totally += planted
            self.__logger.info(f"Planted {planted} of type {product.name} in garden {garden.id}")
        
        self.__stock.update_number_in_stock()

        return planted_totally

    
    
    def grow_anything(self):
        for product_id, product_data in self.__stock.get_ordered_stock_list('amount').items():
            product = self.__product_information.get_product_by_id(product_id)
            if product.is_plantable and product.is_plant(): 
                if self.grow_plants_in_gardens_by_name(product.name, product_data['amount']) == 0 and product.sx == 1 and product.sy == 1:
                    return
            

    def get_plants_in_garden(self) -> garden.Garden:
        gardens = []
        for garden in self.__user.gardens:
            garden.update_planted_fields()
            gardens.append(garden.fields)
        return gardens

    def number_of_plants_in_garden(self) -> dict:
        plant_count = Counter()
        for garden in self.get_plants_in_garden():
            plant_count =  plant_count + Counter(r[1] for r in garden)
        return dict(plant_count)

    def destroy_weed_fields_in_garden(self) -> None:
        for garden in self.__user.gardens:
            garden.destroy_weed_fields(self.__user.user_data.bar)
    
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
                self.__logger.debug(f"No product of id {product.id} planted")
            self.__logger.debug(f" missing amount: {value-stock} {product.name}")
            if value-stock > 0:
                missing_quest_amount.update({product.name: value-stock})
        return missing_quest_amount

    def plant_according_to_quest(self, quest_type_name: str):
        quest_level =""
        try:
            if quest_type_name == quest.CityQuest.__name__:
                quest_level = self.__city_quest
            elif quest_type_name == quest.ParkQuest.__name__:
                if self.__user.town_park_available:
                    quest_level = self.__park_quest
                else:
                    self.__logger.error("Town Park is not available")
            elif quest_type_name == quest.DecoGardenQuest.__name__:
                if self.__user.deco_garden_available:
                    quest_level = self.__deco_garden_quest
            elif quest_type_name == quest.BeesGardenQuest.__name__:
                if self.__user.honey_farm_available:
                    quest_level = self.__bee_farm_quest
                else:
                    self.__logger.error("Honey Farm is not available")
            elif quest_type_name == quest.TreeQuest.__name__:
                quest_level = self.__tree_quest
            else:
                raise NameError(f"No Element named {quest_type_name}")
        except quest.QuestError as e:
            self.__logger.error(e)
        try:
            missing_amount = self.get_missing_quest_amount(quest=quest_level)
            for product_name, amount in missing_amount.items():
                self.grow_plants_in_gardens_by_name(product_name, amount)
        except:
            pass
    
    
    def get_all_wimps_products(self) -> dict:
        all_wimps_products = Counter()
        for garden in self.__user.gardens:
            wimp_data = garden.get_wimps_data()
            for products in wimp_data.values():
                all_wimps_products.update(products[1])

        return dict(all_wimps_products)

    def sell_wimps_products(self, minimal_balance, percentage):
        stock_list = self.__stock.get_ordered_stock_list('amount')
        wimps_data = []
        for garden in self.__user.gardens:
            for wimp_data in garden.get_wimps_data():
                wimps_data.append(wimp_data)

        for wimp in wimps_data:
                if not self.check_wimps_profitable(wimp, percentage):
                    self.__user.decline_wimp(wimp.id)
                else:
                    if self.check_wimps_required_amount(minimal_balance, wimp.product_amount, stock_list):
                        self.__logger.info(f"Selling products to wimp: {wimp.id}")
                        new_products_counts = self.__user.sell_products_to_wimp(wimp.id)
                        for id, amount in wimp.product_amount.items():
                            stock_list[id]['amount'] -= amount
                    else:
                        pass


    def check_wimps_profitable(self, wimp: wimp.Wimp, percentage: int) -> bool:
        npc_sum = 0
        for id, amount in wimp.product_amount.items():
            npc_sum += self.__product_information.get_product_by_id(id).price_npc * amount
        if wimp.reward / npc_sum >= percentage:
            to_sell = True
        else:
            to_sell = False
        return to_sell

    def check_wimps_required_amount(self, minimal_balance, products, stock_list):
        to_sell = True
        for id, amount in products.items():
            product = self.__product_information.get_product_by_id(id)
            minimal_balance = max(self.__notes.get_min_stock(), self.__notes.get_min_stock(product.name), minimal_balance)
            if id not in stock_list:
                to_sell = False
                break
            if stock_list.get(id)['amount'] - (amount + minimal_balance) <= 0:
                to_sell = False
                break
        return to_sell
    
    def sell_on_marketplace_with_min_stock(self,minimal_balance:int =0):
        cash = self.__user.user_data.bar
        products = self.__stock.get_ordered_stock_list('amount', True)
        for id, product_data in products.items():
            minimal_balance = max(self.__notes.get_min_stock(), self.__notes.get_min_stock(product_data['name']), minimal_balance)
            sellable_amount = product_data['amount'] - minimal_balance
            cheapest_offer = self.__marketplace.get_cheapest_offer(int(id))
            if cheapest_offer == None:
                self.__logger.info(f"No offers for {self.__product_information.get_product_by_id(id).name}")
            if sellable_amount > 0 and cheapest_offer!=None:
                price_per_unit = min((cheapest_offer-self.__marketplace.MINIMAL_DISCOUNT),self.__product_information.get_product_by_id(int(id)).price_npc)
                marketplace_fees = price_per_unit*sellable_amount*self.__marketplace.FEE_PERCENTAGE
                if cash >= marketplace_fees:
                    self.__marketplace.sell_on_market(id, price_per_unit,sellable_amount)
                elif cash >= price_per_unit:
                    self.__marketplace.sell_on_market(id, price_per_unit,cash//(price_per_unit*self.__marketplace.FEE_PERCENTAGE))
                else:
                    self.__logger.debug(f"Could not sell anything because {cash} is not enough for the fees to sale a single item")






class NotStartedException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

