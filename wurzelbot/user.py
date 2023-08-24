import logging
import re

import garden
import http_connection
import town_park
from wimp import WimpOrigin


class User:
    def __init__(self, http_connection: http_connection.HTTPConnection):
        self.__http_connection = http_connection
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__account_login = None
        self.__username = None
        self.__user_id = self.__http_connection.user_id
        self.__number_of_gardens = None
        self.__gardens = []
        self.__town_park = None
        self.__user_data = None
        self.__honey_farm_available = False
        self.__aqua_garden_available = False
        self.__town_park_available = False
        self.__mail_addresse_confirmed = False
        self.__deco_garden_available = False
        self.__get_username_from_server()
        self.__get_user_data_from_server()
        self.__init_gardens()
        self.aqua_garden_available = self.is_aqua_garden_available()
        self.honey_farm_available = self.is_honey_farm_available()
        self.town_park_available = self.is_town_park_available()
        if self.__town_park_available:
            self.__town_park = town_park.TownPark(http_connection, 1)
        self.deco_garden_available = self.is_deco_garden_available()
        self.mail_address_confirmed = self.is_mail_address_confirmed()

    @property
    def account_login(self):
        return self.__account_login

    @account_login.setter
    def account_login(self, account_login):
        self.__account_login = account_login

    @property
    def username(self):
        return self.__username

    @username.setter
    def username(self, username: str):
        self.__username = username

    @property
    def user_id(self):
        return self.__user_id

    @user_id.setter
    def user_id(self, identifier):
        self.__user_id = identifier

    @property
    def number_of_gardens(self):
        return self.__number_of_gardens

    @number_of_gardens.setter
    def number_of_gardens(self, number: int):
        if number < 0 or number > 5:
            raise ValueError("Wrong number of gardens provided")
        self.__number_of_gardens = number
        for i in range(1, self.__number_of_gardens + 1):
            self.__gardens.append(garden.Garden(self.__http_connection, i))

    @property
    def user_data(self):
        return self.__user_data

    @user_data.setter
    def user_data(self, data):
        self.__user_data = data

    @property
    def honey_farm_available(self):
        return self.__honey_farm_available

    @honey_farm_available.setter
    def honey_farm_available(self, honey: bool):
        self.__honey_farm_available = honey

    @property
    def aqua_garden_available(self):
        return self.__aqua_garden_available

    @aqua_garden_available.setter
    def aqua_garden_available(self, aqua: bool):
        self.__aqua_garden_available = aqua

    @property
    def town_park_available(self):
        return self.__town_park_available

    @town_park_available.setter
    def town_park_available(self, town: bool):
        self.__town_park_available = town

    @property
    def deco_garden_available(self):
        return self.__deco_garden_available

    @deco_garden_available.setter
    def deco_garden_available(self, deco_garden: bool):
        self.__deco_garden_available = deco_garden

    @property
    def mail_addresse_confirmed(self):
        return self.__mail_addresse_confirmed

    @mail_addresse_confirmed.setter
    def mail_addresse_confirmend(self, confirmend: bool):
        self.__mail_addresse_confirmed = confirmend

    def __get_username_from_server(self):
        jcontent = self.__http_connection.get_username_from_server()
        self.__username = self.__get_username_from_json_content(jcontent)
        self.__logger.info("Username: " + self.__username)

    def __get_user_data_from_server(self):
        jcontent = self.__http_connection.read_user_data_from_server()
        user_data = get_user_data_from_json_content(jcontent)
        self.__user_data = user_data
        return user_data

    def __init_gardens(self):
        """
        Ermittelt die Anzahl der Gärten und initialisiert alle.
        """
        jcontent = self.__http_connection.execute_command(
            f"do=statsGetStats&which=0&start=0&additional={self.__user_id}"
        )

        result = False
        for i in range(0, len(jcontent["table"])):
            s_garten_anz = str(jcontent["table"][i])
            if "Gärten" in s_garten_anz:
                s_garten_anz = s_garten_anz.replace("<tr>", "")
                s_garten_anz = s_garten_anz.replace("<td>", "")
                s_garten_anz = s_garten_anz.replace("</tr>", "")
                s_garten_anz = s_garten_anz.replace("</td>", "")
                s_garten_anz = s_garten_anz.replace("Gärten", "")
                s_garten_anz = s_garten_anz.strip()
                tmp_number_of_gardens = int(s_garten_anz)
                result = True
                break

        if result:
            self.number_of_gardens = tmp_number_of_gardens

    def __get_number_of_gardens(self):
        jcontent = self.__http_connection.execute_command(
            f"do=statsGetStats&which=0&start=0&additional={self.__user_id}"
        )
        number_of_gardens = self.__get_number_of_gardens_from_json_content(jcontent)
        return number_of_gardens

    def __go_to_bees(self):
        jcontent = self.__http_connection.execute_command("do=bees_init")
        return jcontent

    def __go_to_town_park(self):
        jcontent = self.__http_connection.execute_command("do=park_init")
        return jcontent

    def __get_number_of_gardens_from_json_content(self, jcontent):
        """
        Sucht im übergebenen JSON Objekt nach der Anzahl der Gärten und gibt diese zurück.
        """
        result = False
        for i in range(0, len(jcontent["table"])):
            s_garten_anz = str(jcontent["table"][i])
            if "Gärten" in s_garten_anz:
                s_garten_anz = s_garten_anz.replace("<tr>", "")
                s_garten_anz = s_garten_anz.replace("<td>", "")
                s_garten_anz = s_garten_anz.replace("</tr>", "")
                s_garten_anz = s_garten_anz.replace("</td>", "")
                s_garten_anz = s_garten_anz.replace("Gärten", "")
                s_garten_anz = s_garten_anz.strip()
                number_gardens = int(s_garten_anz)
                result = True
                break

        if result:
            return number_gardens
        self.__logger.debug(jcontent["table"])

    def __get_username_from_json_content(self, jcontent):
        """
        Searches for the username in the passed JSON object and returns it.
        """
        result = False
        for i in range(0, len(jcontent["table"])):
            s_username = str(jcontent["table"][i])
            if "Spielername" in s_username:
                s_username = s_username.replace("<tr>", "")
                s_username = s_username.replace("<td>", "")
                s_username = s_username.replace("</tr>", "")
                s_username = s_username.replace("</td>", "")
                s_username = s_username.replace("Spielername", "")
                s_username = s_username.replace("&nbsp;", "")
                s_username = s_username.strip()
                result = True
                break
        if result:
            return s_username
        self.__logger.error("Username not found")

    def is_honey_farm_available(self):
        if self.__user_data.level_number < 10:
            return False
        jcontent = self.__http_connection.execute_command("do=citymap_init")
        return bool(jcontent["data"]["location"]["bees"]["bought"])

    def is_town_park_available(self):
        if self.__user_data.level_number < 5:
            return False
        jcontent = self.__http_connection.execute_command("do=citymap_init")
        if not jcontent["data"]["location"]["park"]["bought"]:
            return False
        return bool(jcontent["data"]["location"]["park"]["bought"]["parkid"])

    def is_aqua_garden_available(self):
        if self.__user_data.level_number < 19:
            return False
        jcontent = self.__http_connection.get_trophies()
        result = re.search(
            r"trophy_54.png\);[^;]*(gray)[^;^class$]*class", jcontent["html"]
        )
        return result is not None

    def is_deco_garden_available(self):
        if self.__user_data.level_number < 13:
            return False
        jcontent = self.__http_connection.execute_command("do=citymap_init")
        return bool(jcontent["data"]["location"]["decogarden"]["bought"])

    def is_mail_address_confirmed(self):
        content = self.__http_connection.get_user_profile()
        result = re.search(r"Unbestätigte Email:", content)
        return result is not None

    @property
    def gardens(self):
        return self.__gardens

    @property
    def town_park(self):
        if self.__town_park is None:
            raise ValueError("TownPark now available yet!")
        return self.__town_park

    def get_daily_login_bonus(self):
        jcontent = self.__http_connection.read_user_data_from_server()
        bonus_data = jcontent["dailyloginbonus"]
        for day, bonus in bonus_data["data"]["rewards"].items():
            if any(_ in bonus for _ in ("money", "products")):
                self.__http_connection.execute_command(
                    f"do=dailyloginbonus_getreward&day={day}"
                )

    def sell_products_to_wimp(self, wimp_id, wimp_origin: WimpOrigin):
        if wimp_origin == WimpOrigin.GARDEN:
            return self.__http_connection.execute_wimp_command(
                f"do=accept&id={wimp_id}"
            )["newProductCounts"]
        elif wimp_origin == WimpOrigin.BEES_FARM:
            return self.__http_connection.execute_command(
                f"do=bees_wimpshandle&id={wimp_id}&status=1"
            )
        else:
            raise ValueError("Wrong Type of WimpOrigin")

    def decline_wimp(self, wimp_id, wimp_origin: WimpOrigin):
        if wimp_origin == WimpOrigin.GARDEN:
            return self.__http_connection.execute_wimp_command(
                f"do=decline&id={wimp_id}"
            )["action"]
        elif wimp_origin == WimpOrigin.BEES_FARM:
            return self.__http_connection.execute_command(
                f"do=bees_wimpshandle&id={wimp_id}&status=2"
            )
        else:
            raise ValueError("Wrong Type of WimpOrigin")


class UserDataBuilder:
    def __init__(self):
        self.__level_number = None
        self.__level = None
        self.__bar_money = None
        self.__coins = None
        self.__points = None
        self.__mail = None
        self.__contracts = None
        self.__g_tag = None
        self.__time = None

    @property
    def time(self):
        return self.__time

    @time.setter
    def time(self, time):
        self.__time = time

    @property
    def g_tag(self):
        return self.__g_tag

    @g_tag.setter
    def g_tag(self, g_tag):
        self.__g_tag = g_tag

    @property
    def level_number(self):
        return self.__level_number

    @level_number.setter
    def level_number(self, level_number):
        self.__level_number = level_number

    @property
    def level(self):
        return self.__level

    @level.setter
    def level(self, level):
        self.__level = level

    @property
    def bar_money(self):
        return self.__bar_money

    @bar_money.setter
    def bar_money(self, bar_money):
        self.__bar_money = bar_money

    @property
    def coins(self):
        self.__coins

    @coins.setter
    def coins(self, coins):
        self.__coins = coins

    @property
    def points(self):
        return self.__points

    @points.setter
    def points(self, points):
        self.__points = points

    @property
    def mail(self):
        return self.__mail

    @mail.setter
    def mail(self, mail: str):
        self.__mail = mail

    @property
    def contracts(self):
        return self.__contracts

    @contracts.setter
    def contracts(self, contracts):
        self.__contracts = contracts

    def build(self):
        return UserData(self)


def get_user_data_from_json_content(content):
    """
    Ermittelt userdaten aus JSON Content.
    """

    builder = UserDataBuilder()
    builder.level_number = int(content["levelnr"])
    builder.bar_money = float(content["bar_unformat"])
    builder.coins = int(content["coins"])
    builder.level = str(content["level"])
    builder.points = int(content["points"])
    builder.mail = int(content["mail"])
    builder.contracts = int(content["contracts"])
    builder.g_tag = str(content["g_tag"])
    builder.time = int(content["time"])

    user_data = UserData(builder)

    return user_data


class UserData:
    def __init__(self, builder: UserDataBuilder):
        self.__mail = None
        self.__level_number = builder.level_number
        self.__level = builder.level
        self.__bar = builder.bar_money
        self.__coins = builder.coins
        self.__points = builder.points
        self.__mail = builder.mail
        self.__contracts = builder.contracts
        self.__g_tag = builder.g_tag
        self.__time = builder.time

    @property
    def time(self):
        return self.__time

    @property
    def contracts(self):
        return self.__contracts

    @property
    def mail(self):
        return self.__mail

    @property
    def points(self):
        return self.__points

    @property
    def coins(self):
        self.__coins

    @property
    def bar(self):
        return self.__bar

    @property
    def level(self):
        return self.__level

    @property
    def level_number(self):
        return self.__level_number
