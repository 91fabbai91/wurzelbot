from ast import arg
import logging
import yaml
import io
import sys
from distutils.command.config import config
from enum import Enum
import argparse
from wurzelbot import Wurzelbot
from login_data import LoginData

#needs to get help texts and how parameters needs to be used
class Task(object):
    def __init__(self, name:str, description:str) -> None:
        self.__name = name
        self.__description = description

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
    GROW_FOR_QUESTS = Task("grow_for_quests","Grow plants for quests and set the quest you want to grow for in config.yaml")
    GROW_PLANTS = Task("grow_plants", "Grow specific plants in your gardens")
    START_BEES_TOUR = Task("start_bees_tour", "Start the bees to fly out of their hive")
    FARM_TOWN_PARK = Task("farm_town_park","To go to the Town Park, empty the cashier and renew items if possibl")
    SELL_WIMPS_PERCENTAGE = Task("sell_to_wimps_percentage","Sell stuff to Wimps if their offer is higher than the percentage from marketplace")
    SELL_ON_MARKETPLACE = Task("sell_on_marketplace","Sell stuff to the marketplace until the minimal amount defined here is reached")



if __name__ == "__main__":
    default_config_path = 'config/config.yaml'
    parser = argparse.ArgumentParser(description='Wurzelimperium Bot - the pythonic way')
    parser.add_argument('--configFile',default=argparse.SUPPRESS, help="absolute config file path")


    args, left_overs = parser.parse_known_args()
    if('configFile' in args):
        config_path = args.configFile
    else:
        config_path = default_config_path
    try:
        config_file = io.FileIO(config_path,'r')
        config = yaml.safe_load(config_file)
    except:
        raise NoConfigFoundError(f"No Config in path {config_path} available . Default config file is {config}")
    

    
    logging.basicConfig(level=config['logging']['level'],handlers=[
        logging.FileHandler(config['logging']['filename']),
        logging.StreamHandler(sys.stdout)],
        format='%(asctime)s - %(message)s')
    login_data = LoginData(config['logins']['server'], config['logins']['name'],config['logins']['password'])
    wurzelbot = Wurzelbot()
    wurzelbot.start_wurzelbot(login_data)
    wurzelbot.harvest_all_garden()
    wurzelbot.destroy_weed_fields_in_garden()
    if 'tasks' not in config:
        logging.info(f'There are different tasks possible to use. These are:')
        for x in Tasks:
            logging.info(f'{x.value}')
    else:
        for task in config['tasks']:
            if  Tasks.GROW_FOR_QUESTS.value.name in str(task):
                if wurzelbot.has_empty_fields():
                    for quest_name in task[Tasks.GROW_FOR_QUESTS.value.name]:
                        wurzelbot.plant_according_to_quest(quest_name)
            elif Tasks.GROW_PLANTS.value.name in task:
                if wurzelbot.has_empty_fields():
                    for plant in task[Tasks.GROW_PLANTS.value.name]:
                        wurzelbot.grow_plants_in_gardens_by_name(plant)
            elif Tasks.START_BEES_TOUR.value.name in task:
                wurzelbot.start_all_bees_tour()
            elif Tasks.FARM_TOWN_PARK.value.name in task:
                wurzelbot.collect_cash_from_park()
                wurzelbot.renew_all_items_in_park()
            elif(Tasks.SELL_WIMPS_PERCENTAGE.value.name in task):
                percentage = float(task[Tasks.SELL_WIMPS_PERCENTAGE.value.name])/100.0
                wurzelbot.sell_wimps_products(0,percentage)
            elif((Tasks.SELL_ON_MARKETPLACE.value.name in task)):
                wurzelbot.sell_on_marketplace_with_min_stock(int(task[Tasks.SELL_ON_MARKETPLACE.value.name]))
            else:
                logging.error(f"No Task found with name {task}")
    if wurzelbot.has_empty_fields():
        wurzelbot.grow_anything()
    wurzelbot.water_plants_in_all_gardens()
    wurzelbot.get_daily_login_bonus()
    wurzelbot.stop_wurzelbot()

class NoConfigFoundError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)