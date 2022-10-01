import logging
from enum import Enum, unique
from . import http_connection

@unique
class BeesTour(Enum):
    TWO_HOURS_TOUR = 1
    EIGHT_HOURS_TOUR = 2
    TWENTYFOUR_HOURS_TOUR =3


class BeesFarm(object):
    def __init__(self, http_connection: http_connection.HTTPConnection) -> None:
        self.__http_connection = http_connection
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__hives = []
        self.__setup_bees_farm()

    @property
    def hives(self):
        return self.__hives

    def __setup_bees_farm(self):
        bee_state = self.__go_to_bees()
        for index ,hive in bee_state['data']['data']['hives'].items():
            try:
                if hive['time']:
                    self.__hives.append(hive)
                    self.__logger.debug("Added Hive with id {index}".format(index=index))
            except:
                pass
    

    def __go_to_bees(self):
        jcontent = self.__http_connection.execute_command('do=bees_init')
        return jcontent

    def start_bees_tour(self, beehive_id: int, tour: BeesTour):
        self.__go_to_bees()
        self.__http_connection.execute_command('do=bees_startflight&id={beehive_id}&tour={tour}'.format(beehive_id=beehive_id, tour=tour.value))

    def start_all_bees_tour(self, tour: BeesTour):
        for index, hive in enumerate(self.__hives):
            if hive['tour_remain']<0:
                self.start_bees_tour(index+1,tour)
                
    