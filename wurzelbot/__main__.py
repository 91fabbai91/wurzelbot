from ast import arg
import logging
import yaml
import io
import sys
from distutils.command.config import config
import argparse
from wurzelbot import Wurzelbot
from login_data import LoginData
from quest import CityQuest, ParkQuest, DecoGardenQuest


if __name__ == "__main__":
    default_config_path = 'config/config.yaml'
    parser = argparse.ArgumentParser(description='Wurzelimperium Bot - the pythonic way')
    parser.add_argument('--configFile',default=argparse.SUPPRESS, help="absolute config file path")
    parser.add_argument('--growPlants', default=argparse.SUPPRESS,nargs='*')
    parser.add_argument('--growForQuests', default=argparse.SUPPRESS,nargs='*')
    parser.add_argument('--farmTownPark', default=argparse.SUPPRESS, action='store_true')
    parser.add_argument('--startBeesTour', default=argparse.SUPPRESS, action='store_true')
    parser.add_argument('--sellToWimpsPercentage',default=argparse.SUPPRESS, help="percentage of wimp price to npc price")


    args, left_overs = parser.parse_known_args()
    if('configFile' in args):
        config_path = args.configFile
    else:
        config_path = default_config_path#
    try:
        config_file = io.FileIO(config_path,'r')
        config = yaml.safe_load(config_file)
    except:
        raise NoConfigFoundError("No Config in path {given_config} available . Default config file is {config}".format(config=default_config_path, give_config=config_path))
    

    
    logging.basicConfig(level=config['logging']['level'],handlers=[
        logging.FileHandler(config['logging']['filename']),
        logging.StreamHandler(sys.stdout)],
        format='%(asctime)s - %(message)s')
    login_data = LoginData(config['logins']['server'], config['logins']['name'],config['logins']['password'])
    wurzelbot = Wurzelbot()
    wurzelbot.start_wurzelbot(login_data)
    wurzelbot.sell_on_market("Zwiebel",1.76,100)
    wurzelbot.harvest_all_garden()
    if('growForQuests' in args):
        for quest_name in args.growForQuests:
            wurzelbot.plant_according_to_quest(quest_name)
    elif('growPlants' in args):
        for plant in args.growPlants:
            wurzelbot.grow_plants_in_gardens_by_name(plant)
    else:
        wurzelbot.grow_anything()
    wurzelbot.water_plants_in_all_gardens()
    if('startBeesTour' in args):
        wurzelbot.start_all_bees_tour()
    if('farmTownPark' in args):
        wurzelbot.collect_cash_from_park()
        wurzelbot.renew_all_items_in_park()
    if('sellToWimpsPercentage' in args):
        wurzelbot.sell_wimps_products(0,args.sellToWimpsPercentage)
    wurzelbot.get_daily_login_bonus()
    
    wurzelbot.stop_wurzelbot()

class NoConfigFoundError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)