import logging
import re

import http_connection


class Notes:
    def __init__(self, http_connection: http_connection.HTTPConnection):
        self.__http_connection = http_connection
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__min_stock = {}
        self.__get_initial_min_stock()

    def get_notes(self):
        return self.__http_connection.get_notes()

    def __get_initial_min_stock(self):
        note = self.get_notes()
        if note is None:
            return
        note = note.replace("\r\n", "\n")
        lines = note.split("\n")
        regexp = re.compile(r"minStock\((.*?)\)")

        for line in lines:
            if line.strip() == "":
                continue
            if line.startswith("minStock:"):
                min_amount = self.__extract_amount(line, "minStock:")
                self.__min_stock.update({"ALL": min_amount})

            if regexp.search(line):
                plant_name = regexp.findall(line)[0]
                min_amount = self.__extract_amount(line, f"minStock({plant_name}):")
                self.__min_stock.update({plant_name: min_amount})

    def get_min_stock(self, plant_name=None):
        if plant_name is None:
            min_stock = self.__min_stock.get("ALL")
        else:
            min_stock = self.__min_stock.get(plant_name)
        if min_stock is None:
            return 0
        return min_stock

    def __extract_amount(self, line, prefix):
        min_stock_str = line.replace(prefix, "").strip()
        min_stock_int = 0
        try:
            min_stock_int = int(min_stock_str)
        except:
            self.__logger.error(f'Error: "{prefix}" must be an int')
        return min_stock_int
