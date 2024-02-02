import logging
import sys

from login_data import LoginData

from config import Settings
from wurzelbot import Wurzelbot

if __name__ == "__main__":
    settings = Settings()
    logging.basicConfig(
        level=settings.logging.level,
        handlers=[
            logging.FileHandler(settings.logging.filename),
            logging.StreamHandler(sys.stdout),
        ],
        format="%(asctime)s - %(message)s",
    )
    login_data = LoginData(
        server=settings.logins.server,
        username=settings.logins.name,
        password=settings.logins.password,
    )
    wurzelbot = Wurzelbot()
    product_information_filename = settings.product_information_filename

    wurzelbot.start_wurzelbot(login_data, product_information_filename)
    wurzelbot.get_daily_login_bonus()
    wurzelbot.harvest_all_garden()
    wurzelbot.destroy_weed_fields_in_garden()
    wurzelbot.destroy_weed_fields_in_town_park()
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
    percentage = float(settings.tasks.sell_to_wimps_percentage) / 100.0
    wurzelbot.sell_wimps_products(0, percentage)
    if settings.tasks.sell_on_marketplace is not None:
        wurzelbot.sell_on_marketplace_with_min_stock(
            int(settings.tasks.sell_on_marketplace.min_stock)
        )
    if wurzelbot.has_empty_fields():
        wurzelbot.grow_anything()
    wurzelbot.water_plants_in_all_gardens()
    wurzelbot.stop_wurzelbot()
