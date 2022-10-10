import logging
import http_connection
from enum import Enum

class TownPark(object):
    def __init__(self, http_connection: http_connection.HTTPConnection, park_id: int):
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__http_connection = http_connection
        self.__id = park_id

    @property
    def id(self):
        return self.__id

    def __go_to_park(self):
        return self.__http_connection.execute_command('do=park_init')



    def collect_cash_points_from_park(self):
        self.__go_to_park()
        jcontent = self.__http_connection.execute_command('do=park_clearcashpoint')
        return jcontent["data"]["data"]["cashpoint"]

    def __get_renewable_deko_from_park(self):
        jcontent = self.__go_to_park()
        items = jcontent["data"]["data"]["park"][str(self.__id)]["items"]
        renewableItems = {}
        for i, item in items.items():

            if item["remain"] < 0:
                renewableItems.update({i:item})
        return renewableItems

    def get_blocked_fields(self):
        jcontent = self.__go_to_park()
        return self.__get_blocked_fields_from_json(jcontent)
    
    def __get_blocked_fields_from_json(self,jcontent):
        blocked_fields = {}
        
        fields = jcontent["data"]["data"]["park"][int(self.__id)]["ground"]
        for i,field in enumerate(fields):
            if field["item"].startswith("trash"):
                blocked_field_type = field["item"][-len("trash"):]
                blocked_fields.update({int(i), BlockedFieldType(int(blocked_field_type))})
        return blocked_fields

    def __renew_items_in_park(self, item_tile):
        self.__http_connection.execute_command('park_renewitem&parkid=' + str(self.__id) \
                + '&tile=' + str(item_tile))

    def renew_all_items_in_park(self):
        for item in self.__get_renewable_deko_from_park():
            self.__renew_items_in_park(item)

class BlockedFieldType(Enum):
    WEED = 1
    TREE_STUMP = 2
    STONE = 3
