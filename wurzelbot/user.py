from distutils.command.build import build
import http_connection
import garden
import logging
import re
import time

class User(object):
    def __init__(self, http_connection: http_connection.HTTPConnection):
        self.__http_connection = http_connection
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__account_login = None
        self.__username = None
        self.__user_id = self.__http_connection.user_id
        self.__number_of_gardens = None
        self.__gardens = []
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
        self.deco_garden_available = self.is_deco_garden_available()
        self.mail_address_confirmed = self.is_mail_address_confirmed()
    
    @property
    def account_login(self):
        return self.__account_login

    @account_login.setter
    def account_login(self, al):
        self.__account_login = al

    @property
    def username(self):
        return self.__username

    @username.setter
    def username(self, u: str):
        self.__username = u

    @property
    def user_id(self):
        return self.__user_id

    @user_id.setter
    def user_id(self, id):
        self.__user_id = id
    
    @property
    def number_of_gardens(self):
        return self.__number_of_gardens

    @number_of_gardens.setter
    def number_of_gardens(self, nr: int):
        if(nr<0 or nr >5):
            raise ValueError("Wrong number of gardens provided")
        self.__number_of_gardens = nr
        for i in range(1,self.__number_of_gardens+1):
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
        self.__username = self.__http_connection.get_username_from_server()
        self.__logger.info("Username: " + self.__username)

    def __get_user_data_from_server(self):
        jcontent = self.__http_connection.read_user_data_from_server()
        user_data= self.__get_user_data_from_json_content(jcontent)
        self.__user_data = user_data
        return user_data

    def __get_user_data_from_json_content(self, content):
        """
        Ermittelt userdaten aus JSON Content.
        """
        
        builder = UserDataBuilder()
        builder.level_number = int(content['levelnr'])
        builder.bar = str(content['bar'])
        builder.coins = int(content['coins'])
        builder.level = str(content['level'])
        builder.points = int(content['points'])
        builder.mail = int(content['mail'])
        builder.contracts = int(content['contracts'])
        builder.g_tag = str(content['g_tag'])
        builder.time = int(content['time'])

        user_data = UserData(builder)

        return user_data

    def __init_gardens(self):
        """
        Ermittelt die Anzahl der Gärten und initialisiert alle.
        """
        jContent = self.__http_connection.execute_command(f'do=statsGetStats&which=0&start=0&additional={self.__user_id}')

        result = False
        for i in range(0, len(jContent['table'])):
            sGartenAnz = str(jContent['table'][i])   
            if 'Gärten' in sGartenAnz:
                sGartenAnz = sGartenAnz.replace('<tr>', '')
                sGartenAnz = sGartenAnz.replace('<td>', '')
                sGartenAnz = sGartenAnz.replace('</tr>', '')
                sGartenAnz = sGartenAnz.replace('</td>', '')
                sGartenAnz = sGartenAnz.replace('Gärten', '')
                sGartenAnz = sGartenAnz.strip()
                tmp_number_of_gardens = int(sGartenAnz)
                result = True
                break

        if result:
            self.number_of_gardens = tmp_number_of_gardens


    def __get_number_of_gardens(self):
        jcontent = self.__http_connection.execute_command(f'do=statsGetStats&which=0&start=0&additional={self.__user_id}')
        iNumber = self.__get_number_of_gardens_from_json_content(jcontent)
        return iNumber

    def __go_to_bees(self):
        jcontent = self.__http_connection.execute_command('do=bees_init')
        return jcontent

    def __go_to_town_park(self):
        jcontent = self.__http_connection.execute_command('do=park_init')
        return jcontent


    def __get_number_of_gardens_from_json_content(self, jContent):
        """
        Sucht im übergebenen JSON Objekt nach der Anzahl der Gärten und gibt diese zurück.
        """
        result = False
        for i in range(0, len(jContent['table'])):
            sGartenAnz = str(jContent['table'][i])   
            if 'Gärten' in sGartenAnz:
                sGartenAnz = sGartenAnz.replace('<tr>', '')
                sGartenAnz = sGartenAnz.replace('<td>', '')
                sGartenAnz = sGartenAnz.replace('</tr>', '')
                sGartenAnz = sGartenAnz.replace('</td>', '')
                sGartenAnz = sGartenAnz.replace('Gärten', '')
                sGartenAnz = sGartenAnz.strip()
                iGartenAnz = int(sGartenAnz)
                result = True
                break

        if result:
            return iGartenAnz
        else:
            self.__logger.debug(jContent['table'])

    def is_honey_farm_available(self):
        if self.__user_data.level_number < 10:
            return False
        jContent = self.__http_connection.execute_command('do=citymap_init')
        if jContent['data']['location']['bees']['bought'] == 1:
            return True
        else:
            return False

    def is_town_park_available(self):
        if self.__user_data.level_number < 5:
            return False
        jContent = self.__http_connection.execute_command('do=citymap_init')
        if jContent['data']['location']['park']['bought'] == True:
            return True
        else:
            return False


    
    def is_aqua_garden_available(self):
        if self.__user_data.level_number < 19:
            return False
        jContent = self.__http_connection.get_trophies()
        result = re.search(r'trophy_54.png\);[^;]*(gray)[^;^class$]*class', jContent['html'])
        if result == None:
            return True
        else:
            return False

    def is_deco_garden_available(self):
        if self.__user_data.level_number < 13:
            return False
        jContent = self.__http_connection.execute_command('do=citymap_init')
        if jContent['data']['location']['decogarden']['bought'] == 1:
            return True
        else:
            return False
    def is_mail_address_confirmed(self):
        content = self.__http_connection.get_user_profile()
        result = re.search(r'Unbestätigte Email:', content)
        if (result == None): return True
        else: return False

    @property
    def gardens(self):
        return self.__gardens


    def get_daily_login_bonus(self):
        jcontent = self.__http_connection.read_user_data_from_server()
        bonus_data = jcontent['dailyloginbonus']
        for day, bonus in bonus_data['data']['rewards'].items():
            if any(_ in bonus for _ in ('money', 'products')):
                    self.__http_connection.execute_command(f"do=dailyloginbonus_getreward&day={day}")
    
    def sell_products_to_wimp(self, wimp_id):
        return self.__http_connection.execute_wimp_command(f"do=accept&id={wimp_id}")['newProductCounts']

    def decline_wimp(self, wimp_id):
        return self.__http_connection.execute_wimp_command(f"do=decline&id={wimp_id}")['action']
    
class UserDataBuilder(object):
    def __init__(self):
        self.__level_number = None
        self.__level = None
        self.__bar = None
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
    def time(self, t):
        self.__time = t

    @property
    def g_tag(self):
        return self.__g_tag

    @g_tag.setter
    def g_tag(self, g):
        self.__g_tag = g

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
    def bar(self):
        return self.__bar

    @bar.setter
    def bar(self, bar):
        self.__bar = bar


    @property
    def coins(self):
        self.__coins

    @coins.setter
    def coins(self, c):
        self.__coins = c

    @property
    def points(self):
        return self.__points

    @points.setter
    def points(self, p):
        self.__points = p


    @property
    def mail(self):
        return self.__mail
    
    @mail.setter
    def mail(self, m : str):
        self.__mail = m


    @property
    def contracts(self):
        return self.__contracts

    @contracts.setter
    def contracts(self, c):
        self.__contracts = c

    def build(self):
        return UserData(self)

class UserData(object):
    def __init__(self, builder: UserDataBuilder):
        self.__mail = None
        self.__level_number = builder.level_number
        self.__level = builder.level
        self.__bar = builder.bar
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