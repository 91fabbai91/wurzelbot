import logging
import time
from collections import Counter
from datetime import datetime
from enum import Enum

import http_connection
import parsing_utils
from wimp import Wimp


class BlockedFieldType(Enum):
    WEED = {"id": 41, "costs": 2.5}
    TREE_STUMP = {"id": 42, "costs": 250.0}
    STONE = {"id": 43, "costs": 50.0}
    MOLE = {"id": 45, "costs": 500.0}


class Garden:
    def __init__(self, http_connection: http_connection.HTTPConnection, garden_id: int):
        self.__id = garden_id
        self.__len_x = 17
        self.__len_y = 12
        self.__logger = logging.getLogger(f"Garden{self.__id}")
        self.__http_connection = http_connection
        self.__number_of_fields = self.__len_x * self.__len_y
        self.__fields = []
        self.update_planted_fields()

    @property
    def id(self):
        return self.__id

    @property
    def len_x(self):
        return self.__len_x

    @property
    def len_y(self):
        return self.__len_y

    @property
    def number_of_fields(self):
        return self.__number_of_fields

    @property
    def fields(self):
        return self.__fields

    def number_planted_plants(self, plant_id: int):
        number_plants = 0
        for field in self.__fields:
            if int(field[1]) == plant_id:
                number_plants = number_plants + 1
        return number_plants

    def __get_all_field_ids_from_field_id_and_size_as_string(
        self, field_id: int, s_x: int, s_y: int
    ) -> str:
        """
        Calculates all IDs based on the field_id and size of the plant (sx, sy)
        and returns them as a string.
        """

        # Returned field indices (x) for plants of size 1, 2 and 4 fields.
        # Important when watering; all indices must be specified there.
        # (Both those marked with x and those marked with o).
        # x: field_id
        # o: ergänzte Felder anhand der size
        # +---+   +---+---+   +---+---+
        # | x |   | x | o |   | x | o |
        # +---+   +---+---+   +---+---+
        #                     | o | o |
        #                     +---+---+

        if s_x == 1 and s_y == 1:
            return str(field_id)
        if s_x == 2 and s_y == 1:
            return f"{field_id},{field_id+1}"
        if s_x == 1 and s_y == 2:
            return f"{field_id},{field_id + 17}"
        if s_x == 2 and s_y == 2:
            return f"{field_id},{field_id + 1},{field_id + 17},{field_id + 18}"
        self.__logger.debug(f"Error der plant_size --> sx: {s_x} sy: {s_y}")
        return

    def __get_all_field_ids_from_field_id_and_size_as_int_list(
        self, field_id: int, s_x: int, s_y: int
    ) -> list:
        """
        Calculates all IDs based on the field_id and size of the plant (s_x, s_y)
        and returns them as an integer list.
        """
        s_fields = self.__get_all_field_ids_from_field_id_and_size_as_string(
            field_id, s_x, s_y
        )
        list_fields = s_fields.split(",")  # Stringarray
        list_fields = [int(field) for field in list_fields]
        return list_fields

    def __is_plant_growable_on_field(
        self, field_id: int, empty_fields: list, fields_to_plant: list, s_x: int
    ) -> bool:
        """
        Checks against several criteria to see if planting is possible.
        """
        # Betrachtetes Feld darf nicht besetzt sein
        if field_id not in empty_fields:
            return False

        # Planting must not be done outside the garden
        # The consideration in x-direction is sufficient, because here a
        # "line break" takes place. The y-direction is covered by the
        # query whether all required fields are empty.
        # Fields outside (in y-direction) of the garden are not empty,
        # since they do not exist.

        if not (self.__number_of_fields - field_id) % self.__len_x >= s_x - 1:
            return False
        fields_to_plant_set = set(fields_to_plant)
        empty_fields_set = set(empty_fields)

        # Alle benötigten Felder der Pflanze müssen leer sein
        if not fields_to_plant_set.issubset(empty_fields_set):
            return False
        return True

    def get_empty_fields(self) -> dict:
        jcontent = self.__http_connection.execute_command(
            "do=changeGarden&garden=" + str(self.__id)
        )
        return find_empty_fields_from_json_content(jcontent)

    def get_blocked_fields(self) -> dict:
        jcontent = self.__http_connection.execute_command(
            "do=changeGarden&garden=" + str(self.__id)
        )
        return find_blocked_fields_from_json_content(jcontent)

    def destroy_weed_fields(self, cash: float) -> int:
        number_freed_fields = 0
        blocked_fields = self.get_blocked_fields()
        blocked_fields_type_count = Counter(list(blocked_fields.values()))
        for blocked_field_type in BlockedFieldType:
            try:
                if (
                    blocked_fields_type_count[blocked_field_type.value["id"]] > 0
                    and cash > blocked_field_type.value["costs"]
                ):
                    number_freed_fields = (
                        number_freed_fields
                        + self.__destroy_fields_of_type(
                            blocked_fields, blocked_field_type, cash
                        )
                    )
            except parsing_utils.JSONError as exception:
                self.__logger.error(exception)
            else:
                self.__logger.info(f"Number of freed fields: {number_freed_fields}")
                return number_freed_fields
        return 0

    def __destroy_fields_of_type(
        self, blocked_fields: list, blocked_field_type: BlockedFieldType, cash: float
    ) -> int:
        number_freed_fields = 0
        for field_id, field_type in blocked_fields.items():
            if (
                field_type == blocked_field_type.value["id"]
                and cash >= blocked_field_type.value["costs"]
            ):
                if self.__http_connection.destroy_weed_field(field_id) is not None:
                    number_freed_fields = number_freed_fields + 1
                    cash -= blocked_field_type.value["costs"]

        return number_freed_fields

    def update_planted_fields(self) -> list:
        jcontent = self.__http_connection.execute_command(
            f"do=changeGarden&garden= {self.__id}"
        )
        plants = self.__get_plants_on_fields(jcontent)
        return plants

    def __get_plants_on_fields(self, jcontent: dict) -> list:
        self.__fields = []
        for field in jcontent["grow"]:
            field[3] = datetime.fromtimestamp(int(field[3]))
            self.__fields.append(field)
        return self.__fields

    def harvest(self):
        self.__http_connection.execute_command(f"do=changeGarden&garden={self.__id}")
        status_harvest = self.__http_connection.execute_command("do=gardenHarvestAll")

    def grow_plants(self, plant, s_x: int, s_y: int, amount: int) -> int:
        planted = 0
        empty_fields = self.get_empty_fields()

        try:
            for field in range(1, self.__number_of_fields + 1):
                if planted == amount:
                    break

                fields_to_plant = (
                    self.__get_all_field_ids_from_field_id_and_size_as_int_list(
                        field, s_x, s_y
                    )
                )

                if self.__is_plant_growable_on_field(
                    field, empty_fields, fields_to_plant, s_x
                ):
                    fields = self.__get_all_field_ids_from_field_id_and_size_as_string(
                        field, s_x, s_y
                    )
                    self.__http_connection.grow_plant(
                        field, plant.id, self.__id, fields
                    )
                    planted += 1

                    # Delete occupied fields from the list of empty fields after cultivation
                    fields_to_plant_set = set(fields_to_plant)
                    empty_fields_set = set(empty_fields)
                    tmp_set = empty_fields_set - fields_to_plant_set
                    empty_fields = list(tmp_set)

        except Exception as e:
            self.__logger.error(e)
            self.__logger.error(f"In garden {self.__id} could not get planted.")
            return 0

        msg = (
            f"In garden {self.__id} were {planted} plants of type {plant.name} planted."
        )
        self.__logger.debug(msg)
        return planted

    def __find_plants_to_be_watered_from_json_content(self, jcontent: dict) -> dict:
        """
        Searches the JSON content for plants that can be watered
        and returns them including the plant size.
        """
        plants_to_be_watered = {"fieldID": [], "sx": [], "sy": []}
        for field in range(0, len(jcontent["grow"])):
            planted_field_id = jcontent["grow"][field][0]
            plant_size = jcontent["garden"][str(planted_field_id)][9]
            splitted_plant_size = str(plant_size).split("x")
            s_x = splitted_plant_size[0]
            s_y = splitted_plant_size[1]

            if not self.__is_field_watered(jcontent, planted_field_id):
                field_id_to_be_watered = planted_field_id
                plants_to_be_watered["fieldID"].append(field_id_to_be_watered)
                plants_to_be_watered["sx"].append(int(s_x))
                plants_to_be_watered["sy"].append(int(s_y))

        return plants_to_be_watered

    def __is_field_watered(self, jcontent: dict, field_id: int) -> bool:
        """
        Ermittelt, ob ein Feld fieldID gegossen ist und gibt True/False zurück.
        Ist das Datum der Bewässerung 0, wurde das Feld noch nie gegossen.
        Eine Bewässerung hält 24 Stunden an. Liegt die Zeit der letzten Bewässerung
        also 24 Stunden + 30 Sekunden (Sicherheit) zurück, wurde das Feld zwar bereits gegossen,
        kann jedoch wieder gegossen werden.
        """
        one_day_in_seconds = (24 * 60 * 60) + 30
        current_time_in_seconds = time.time()
        water_date_in_seconds = int(jcontent["water"][field_id - 1][1])

        if water_date_in_seconds == "0":
            return False
        if (current_time_in_seconds - water_date_in_seconds) > one_day_in_seconds:
            return False
        else:
            return True

    def water_plants(self):
        self.__logger.info(f"Water all plants in garden {self.__id}.")
        try:
            jcontent = self.__http_connection.execute_command(
                f"do=changeGarden&garden= {self.__id}"
            )
            plants = self.__find_plants_to_be_watered_from_json_content(jcontent)
            number_of_plants = len(plants["fieldID"])
            for i in range(0, number_of_plants):
                s_fields = self.__get_all_field_ids_from_field_id_and_size_as_string(
                    plants["fieldID"][i], plants["sx"][i], plants["sy"][i]
                )
                self.__http_connection.water_plant(
                    self.__id, plants["fieldID"][i], s_fields
                )
        except Exception as error:
            self.__logger.error(error)
            self.__logger.error(f"Garden {self.__id} could not get watered.")
        else:
            self.__logger.info(
                f"In garden {self.__id} were {number_of_plants} plants watered."
            )

    def get_wimps_data(self):
        self.__http_connection.execute_command(f"do=changeGarden&garden={self.__id}")
        jcontent = self.__http_connection.execute_wimp_command("do=getAreaData")
        return self.__get_wimps_list_from_json_content(jcontent)

    def __get_wimps_list_from_json_content(self, jcontent: dict) -> list:
        """
        Returns list of growing plants from JSON content
        """
        wimps_list = []
        for wimp in jcontent["wimps"]:
            product_data = {}
            for product in wimp["sheet"]["products"]:
                product_data[str(product["pid"])] = int(product["amount"])
            wimps_list.append(
                Wimp(
                    id=wimp["sheet"]["id"],
                    product_amount=product_data,
                    reward=wimp["sheet"]["sum"],
                )
            )
        return wimps_list


class AquaGarden(Garden):
    def __init__(self, http_connection):
        super(http_connection, 101)

    def water_plants(self):
        """
        Alle Pflanzen im Wassergarten werden bewässert.
        """
        try:
            jcontent = self.__http_connection.getPlantsToWaterInAquaGarden()
            plants = self.__find_plants_to_be_watered_from_json_content(jcontent)
            number_of_plants = len(plants["fieldID"])
            for i in range(0, number_of_plants):
                s_fields = self.__get_all_field_ids_from_field_id_and_size_as_string(
                    plants["fieldID"][i], plants["sx"][i], plants["sy"][i]
                )
                self.__http_connection.waterPlantInAquaGarden(
                    plants["fieldID"][i], s_fields
                )
        except:
            self.__logger.error("Watergarden could not get watered.")
        else:
            self.__logger.info(
                f"In water garden were {number_of_plants} plants watered."
            )

    def harvest(self):
        self.__http_connection.execute_command("do=watergardenHarvestAll")


def find_empty_fields_from_json_content(jcontent: dict) -> list:
    """
    Searches the JSON content for fields that are empty and returns them.
    """
    empty_fields = []

    for field in jcontent["garden"]:
        if jcontent["garden"][field][0] == 0:
            empty_fields.append(int(field))

    # Sorting over an empty array changes object type to None
    if len(empty_fields) > 0:
        empty_fields.sort(reverse=False)

    return empty_fields


def find_blocked_fields_from_json_content(jcontent: dict) -> dict:
    """
    Searches the JSON content for fields that are infested with weeds and returns them.
    """
    weed_fields = {}

    # 41 weed, 42 tree stump, 43 stone, 45 mole
    for field in jcontent["garden"]:
        blocked_field_type = jcontent["garden"][field][0]
        if blocked_field_type in [x.value["id"] for x in BlockedFieldType]:
            weed_fields.update({int(field): blocked_field_type})

    return weed_fields
