import logging
from collections import Counter
from enum import Enum

import http_connection


class BlockedFieldType(Enum):
    WEED = {"id": 1, "costs": 1000}
    TREE_STUMP = {"id": 2, "costs": 10000}
    STONE = {"id": 3, "costs": 30000}


class TownPark:
    def __init__(self, http_connection: http_connection.HTTPConnection, park_id: int):
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__http_connection = http_connection
        self.__id = park_id
        self.__park_points = self.__get_parkpoints()

    @property
    def id(self):
        return self.__id

    def __go_to_park(self):
        return self.__http_connection.execute_command("do=park_init")

    def collect_cash_points_from_park(self):
        self.__go_to_park()
        jcontent = self.__http_connection.execute_command("do=park_clearcashpoint")
        return jcontent["data"]["data"]["cashpoint"]

    def __get_parkpoints(self) -> int:
        jcontent = self.__go_to_park()
        return int(jcontent["data"]["data"]["points"])

    def __get_renewable_deko_from_park(self):
        jcontent = self.__go_to_park()
        items = jcontent["data"]["data"]["park"][str(self.__id)]["items"]
        renewable_items = {}
        for i, item in items.items():
            if item["remain"] < 0:
                renewable_items.update({i: item})
        return renewable_items

    def get_blocked_fields(self):
        jcontent = self.__go_to_park()
        return self.__get_blocked_fields_from_json(jcontent)

    def __get_blocked_fields_from_json(self, jcontent):
        blocked_fields = {}

        fields = jcontent["data"]["data"]["park"][str(self.__id)]["ground"]
        for i, field in fields.items():
            if field["item"].startswith("trash"):
                blocked_field_type = int(field["item"].replace("trash", ""))
                if blocked_field_type in [x.value["id"] for x in BlockedFieldType]:
                    blocked_fields.update({int(i): int(blocked_field_type)})
        return blocked_fields

    def destroy_weed_fields(self) -> int:
        number_freed_fields = 0
        blocked_fields = self.get_blocked_fields()
        blocked_fields_type_count = Counter(list(blocked_fields.values()))
        for blocked_field_type in BlockedFieldType:
            if (
                blocked_fields_type_count[blocked_field_type.value["id"]] > 0
                and self.__park_points > blocked_field_type.value["costs"]
            ):
                number_freed_fields = (
                    number_freed_fields
                    + self.__destroy_fields_of_type(blocked_fields, blocked_field_type)
                )

        self.__logger.debug(
            f"Number of freed fields: {number_freed_fields} in town park {self.__id}"
        )
        return number_freed_fields

    def __destroy_fields_of_type(
        self, blocked_fields: list, blocked_field_type: BlockedFieldType
    ) -> int:
        number_freed_fields = 0
        for field_id, field_type in blocked_fields.items():
            if (
                field_type == blocked_field_type.value["id"]
                and self.__park_points >= blocked_field_type.value["costs"]
            ):
                if self.__remove_blocked_field(field_id) is not None:
                    number_freed_fields = number_freed_fields + 1
                    self.__park_points -= blocked_field_type.value["costs"]

        return number_freed_fields

    def __remove_blocked_field(self, field_id):
        return self.__http_connection.execute_command(
            f"do=park_removetrash&parkid={self.__id}&tile={field_id}"
        )

    def __renew_items_in_park(self, item_tile):
        self.__http_connection.execute_command(
            f"do=park_renewitem&parkid={self.__id}&tile={item_tile}"
        )

    def renew_all_items_in_park(self):
        for item in self.__get_renewable_deko_from_park():
            self.__renew_items_in_park(item)

    def remove_blocked_field(self, tile: int):
        self.__http_connection.execute_command(
            f"do=park_removetrash&parkid={self.__id}&tile={tile}"
        )

    def buy_new_item(self, item: str, amount: int):
        self.__http_connection.execute_command(
            f"park_buyitem&item={item}&amount={amount}"
        )
