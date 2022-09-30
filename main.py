from wurzelbot.wurzelbot import Wurzelbot
from wurzelbot.login_data import LoginData
import logging

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    login_data = LoginData(1, "bongomedia",'3df5da34')
    wurzelbot = Wurzelbot()
    wurzelbot.start_wurzelbot(login_data)
    wurzelbot.harvest_all_garden()
    print(wurzelbot.number_of_plants_in_garden())
    wurzelbot.plant_according_to_quest()
    wurzelbot.stop_wurzelbot()