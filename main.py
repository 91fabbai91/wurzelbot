from wurzelbot.wurzelbot import Wurzelbot
from wurzelbot.login_data import LoginData
import logging

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    login_data = LoginData(46, "bongomedia",'3df5da34')
    wurzelbot = Wurzelbot()
    wurzelbot.start_wurzelbot(login_data)
    wurzelbot.get_plants_in_garden()
    wurzelbot.stop_wurzelbot()