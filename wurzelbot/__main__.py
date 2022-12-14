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
    config_path = 'config/config.yaml'
    parser = argparse.ArgumentParser(description='Wurzelimperium Bot - the pythonic way')
    parser.add_argument('--configFile',default=argparse.SUPPRESS)
    parser.add_argument('--growPlants', default=argparse.SUPPRESS,nargs='*')
    parser.add_argument('--growForQuests', default=argparse.SUPPRESS,nargs='*')
    parser.add_argument('--farmTownPark', default=argparse.SUPPRESS, action='store_true')
    parser.add_argument('--startBeesTour', default=argparse.SUPPRESS, action='store_true')


    args, left_overs = parser.parse_known_args()
    if('configFile' in args):
        config_path = "config/" + args.configFile
    config_file = io.FileIO(config_path,'r')
    config = yaml.safe_load(config_file)
    
    logging.basicConfig(level=config['logging']['level'],handlers=[
        logging.FileHandler(config['logging']['filename']),
        logging.StreamHandler(sys.stdout)],
        format='%(asctime)s - %(message)s')
    login_data = LoginData(config['logins']['server'], config['logins']['name'],config['logins']['password'])
    wurzelbot = Wurzelbot()
    wurzelbot.start_wurzelbot(login_data)
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
    
    wurzelbot.stop_wurzelbot()