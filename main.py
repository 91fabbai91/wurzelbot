from distutils.command.config import config
from wurzelbot.wurzelbot import Wurzelbot
from wurzelbot.login_data import LoginData
from wurzelbot.quest import CityQuest, ParkQuest, DecoGardenQuest
import logging
import yaml
import io

if __name__ == "__main__":
    config_file = io.FileIO('config/config.yaml','r')
    config = yaml.safe_load(config_file)
    logging.basicConfig(filename=config['logging']['filename'], level=config['logging']['level'], format='%(asctime)s - %(message)s')
    login_data = LoginData(config['logins']['server'], config['logins']['name'],config['logins']['password'])
    wurzelbot = Wurzelbot()
    wurzelbot.start_wurzelbot(login_data)
    wurzelbot.harvest_all_garden()
    wurzelbot.grow_anything()
    wurzelbot.water_plants_in_all_gardens()
    wurzelbot.collectCashFromPark()
    wurzelbot.renew_all_items_in_park()
    wurzelbot.stop_wurzelbot()