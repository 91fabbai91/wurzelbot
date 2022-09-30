from wurzelbot.wurzelbot import Wurzelbot
from wurzelbot.login_data import LoginData
from wurzelbot.quest import CityQuest, ParkQuest, DecoGardenQuest
import logging

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    login_data = LoginData(2, "bongomedia",'3df5da34')
    wurzelbot = Wurzelbot()
    wurzelbot.start_wurzelbot(login_data)
    wurzelbot.harvest_all_garden()
    wurzelbot.grow_anything()
    wurzelbot.water_plants_in_all_gardens()
    wurzelbot.stop_wurzelbot()