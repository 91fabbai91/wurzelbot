import logging
from enum import Enum, unique

import http_connection
from wimp import Wimp, WimpOrigin


@unique
class BeesTour(Enum):
    TWO_HOURS_TOUR = 1
    EIGHT_HOURS_TOUR = 2
    TWENTYFOUR_HOURS_TOUR = 3


class BeesFarm:
    def __init__(self, http_connection: http_connection.HTTPConnection) -> None:
        self.__http_connection = http_connection
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__hives = {}
        self.__setup_bees_farm()

    @property
    def hives(self):
        return self.__hives

    def __setup_bees_farm(self):
        bee_state = self.__go_to_bees()
        for index, hive in bee_state["data"]["data"]["hives"].items():
            try:
                if hive["time"]:
                    self.__hives[int(index)] = hive
                    self.__logger.debug(f"Added Hive with id {index}")
            except KeyError:
                self.__logger.debug("Key time in hive not found.")
        # sort hives by level
        self.__hives = dict(
            sorted(
                self.__hives.items(), key=lambda hive: hive[1]["level"], reverse=True
            )
        )

    def __go_to_bees(self) -> dict:
        jcontent = self.__http_connection.execute_command("do=bees_init")
        return jcontent

    def start_bees_tour(self, beehive_id: int, tour: BeesTour):
        self.__http_connection.execute_command(
            f"do=bees_startflight&id={beehive_id}&tour={tour.value}"
        )
        self.__logger.debug(
            f"Started bees tour of hive {beehive_id} with duration of {tour.value}"
        )

    def start_all_bees_tour(self, tour: BeesTour):
        jcontent = self.__go_to_bees()
        if jcontent["data"]["stock"] != []:
            for entry in list(jcontent["data"]["stock"].values()):
                if int(entry) == 100000:
                    self.__http_connection.execute_command(f"do=bees_fill")
                    self.__logger.debug("Got Honey")

        for index, hive in self.__hives.items():
            if "tour_remain" not in hive:
                self.start_bees_tour(index, tour)
            elif hive["tour_remain"] < 0:
                self.start_bees_tour(index, tour)

    def get_wimp_data(self) -> list:
        wimps_list = []
        bees_data = self.__go_to_bees()
        wimps = bees_data["data"]["wimps"]
        for wimp in wimps:
            product_data = {}
            for product_id, product_amount in wimp["data"].items():
                product_data.update({product_id: int(product_amount)})
            wimps_list.append(
                Wimp(
                    id=wimp["id"],
                    reward=wimp["price"],
                    product_amount=product_data,
                    origin=WimpOrigin.BEES_FARM,
                )
            )
        return wimps_list

    def __change_bee_hive_product(self, hive_id: int, product_id: int):
        self.__http_connection.execute_command(
            f"do=bees_changehiveproduct&id={hive_id}&pid={product_id}"
        )

    def change_all_bee_hives_product(self, product_id):
        for index, hive in self.__hives.items():
            if int(hive.pid) != product_id:
                self.__change_bee_hive_product(index, int(hive.pid))
