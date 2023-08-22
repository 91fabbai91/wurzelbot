import logging
import sys
from enum import Enum
from pydantic import BaseModel
from wurzelbot import Wurzelbot
from config import Settings
from login_data import LoginData

#needs to get help texts and how parameters needs to be used
class Task(BaseModel):
    name: str
    description: str


    def __repr__(self) -> str:
        return f'Name: {self.__name}, Description: {self.__description}'

    def __str__(self) -> str:
        return f'Name: {self.__name}, Description: {self.__description}'

    @property
    def name(self):
        return self.__name

    @property
    def description(self):
        return self.__description

class Tasks(Enum):
    GROW_FOR_QUESTS = Task(name="grow_for_quests",description="Grow plants for quests and set the quest you want to grow for in config.yaml")
    GROW_PLANTS = Task(name="grow_plants",description="Grow specific plants in your gardens")
    START_BEES_TOUR = Task(name="start_bees_tour", description="Start the bees to fly out of their hive")
    FARM_TOWN_PARK = Task(name="farm_town_park",description="To go to the Town Park, empty the cashier and renew items if possibl")
    SELL_WIMPS_PERCENTAGE = Task(name="sell_to_wimps_percentage",description="Sell stuff to Wimps if their offer is higher than the percentage from marketplace")
    SELL_ON_MARKETPLACE = Task(name="sell_on_marketplace",description="Sell stuff to the marketplace until the minimal amount defined here is reached")



if __name__ == "__main__":  

    settings = Settings()
    logging.basicConfig(level=settings.logging.level,handlers=[
        logging.FileHandler(settings.logging.filename),
        logging.StreamHandler(sys.stdout)],
        format='%(asctime)s - %(message)s')
    login_data = LoginData(server=settings.logins.server, username=settings.logins.name,password=settings.logins.password)
    wurzelbot = Wurzelbot()
    wurzelbot.start_wurzelbot(login_data)
    wurzelbot.get_daily_login_bonus()
    wurzelbot.harvest_all_garden()
    wurzelbot.destroy_weed_fields_in_garden()
    if wurzelbot.has_empty_fields():
        for quest_name in settings.tasks.grow_for_quests:
            wurzelbot.plant_according_to_quest(quest_name)
    if wurzelbot.has_empty_fields():
        for plant in settings.tasks.grow_plants:
            wurzelbot.grow_plants_in_gardens_by_name(plant)
    if settings.tasks.start_bees_tour:
        wurzelbot.start_all_bees_tour()
    if settings.tasks.farm_town_park:
        wurzelbot.collect_cash_from_park()
        wurzelbot.renew_all_items_in_park()
    percentage = float(settings.tasks.sell_to_wimps_percentage)/100.0
    wurzelbot.sell_wimps_products(0,percentage)
    if settings.tasks.sell_on_marketplace is not None:
        wurzelbot.sell_on_marketplace_with_min_stock(int(settings.tasks.sell_on_marketplace.min_stock))
    if wurzelbot.has_empty_fields():
        wurzelbot.grow_anything()
    wurzelbot.water_plants_in_all_gardens()
    wurzelbot.stop_wurzelbot()

class NoConfigFoundError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)