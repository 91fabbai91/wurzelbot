from ast import arg
import logging
import yaml
import io
import sys
from distutils.command.config import config
import argparse
from wurzelbot import Wurzelbot
from login_data import LoginData


if __name__ == "__main__":
    default_config_path = 'config/config.yaml'
    parser = argparse.ArgumentParser(description='Wurzelimperium Bot - the pythonic way')
    parser.add_argument('--configFile',default=argparse.SUPPRESS, help="absolute config file path")


    args, left_overs = parser.parse_known_args()
    if('configFile' in args):
        config_path = args.configFile
    else:
        config_path = default_config_path#
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
    for task in config['tasks']:
        if  'grow_for_quests' in task and wurzelbot.has_empty_fields():
            for quest_name in task['grow_for_quests']:
                wurzelbot.plant_according_to_quest(quest_name)
        elif 'grow_plants' in task and wurzelbot.has_empty_fields():
            for plant in task['grow_plants']:
                wurzelbot.grow_plants_in_gardens_by_name(plant)
        elif 'start_bees_tour' in task:
            wurzelbot.start_all_bees_tour()
        elif 'farm_town_park' in task:
            wurzelbot.collect_cash_from_park()
            wurzelbot.renew_all_items_in_park()
        elif('sell_to_wimps_percentage' in task):
            percentage = float(task['sell_to_wimps_percentage'])/100.0
            wurzelbot.sell_wimps_products(0,percentage)
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