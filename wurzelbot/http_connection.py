
from urllib.parse import urlencode
import re
import io
import time
import httplib2
from math import floor
from http.cookies import SimpleCookie
import session
import logging
from lxml import html, etree
import login_data
import message
import parsing_utils

#Defines
HTTP_STATE_CONTINUE            = 100
HTTP_STATE_SWITCHING_PROTOCOLS = 101
HTTP_STATE_PROCESSING          = 102
HTTP_STATE_OK                  = 200
HTTP_STATE_FOUND               = 302 #moved temporarily
USER_AGENT                     = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36 Vivaldi/2.2.1388.37'
STATIC_DOMAIN                  = ".wurzelimperium.de"
AJAX_PHP                       = '/ajax/ajax.php?'
MESSAGE_API                    = '/nachrichten/new.php'
WATER_API                      = '/save/wasser.php'
PLANT_API                      = '/save/pflanz.php'
DECO_GARDEN_API                = '/ajax/decogardenajax.php'
DESTROY_API                    = '/save/abriss.php?'
MARKET_BOOTH_API               = '/stadt/marktstand.php'
MARKET_API                     = '/stadt/markt.php'
TREE_QUEST_API                 = '/treequestquery.php?'
WIMPS_API                      = '/ajax/verkaufajax.php?'
NOTES_API                      = 'notiz.php'

class HTTPConnection(object):

    # singleton for just one login, due to the backend
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(HTTPConnection, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.__webclient = httplib2.Http(disable_ssl_certificate_validation=True)
        self.__webclient.follow_redirects = False
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__session = session.Session()
        self.__token = None
        self.__user_id = None
        self.__cookie = None

    def __del__(self):
        self.__session = None
        self.__token = None
        self.__user_id = None

    @property
    def user_id(self):
        return self.__user_id

    def login(self, login_data: login_data.LoginData):
        parameter = urlencode({'do': 'login',
                    'server': 'server' + str(login_data.server),
                    'user': login_data.username,
                    'pass': login_data.password}) 
    
        headers = {'Content-type': 'application/x-www-form-urlencoded',
                   'Connection': 'keep-alive'}
        try:
            response, content = self.__webclient.request('https://www.wurzelimperium.de/dispatch.php', \
                                                    'POST', \
                                                    parameter, \
                                                    headers)

            self.__check_if_http_status_is_ok(response)
            jcontent = parsing_utils.generate_json_content_and_check_for_ok(content)
            self.__get_token_from_url(jcontent['url'])
            url = jcontent['url']
            response, content = self.__webclient.request(url, 'GET', headers=headers)
            self.__check_if_http_status_is_found(response)
        except:
            raise
        else:
            cookie = SimpleCookie(response['set-cookie'])
            cookie.load(str(response["set-cookie"]).replace("secure, ", "", -1))
            self.__session.open_session(cookie['PHPSESSID'].value, str(login_data.server))
            self.__cookie = cookie
            self.__user_id = cookie['wunr'].value

    def logout(self):
        headers = {'Cookie': f'PHPSESSID={self.__session.session_id};wunr={self.__user_id}'}
        
        adresse = f'http://s{self.__session.server}{STATIC_DOMAIN}/main.php?page=logout'

        try: #content ist beim Logout leer
            response, content = self.__webclient.request(adresse, 'GET', headers=headers)
            self.__check_if_http_status_is_found(response)
            cookie = SimpleCookie(response['set-cookie'])
            self.__check_if_session_is_deleted(cookie)
        except:
            raise
        else:
            self.__del__()

    def sell_on_market(self, item_id: int , price: float, number: int):
        self.execute_command("do=citymap_init")
        self.__go_to_city()
        self.__get_to_market()
        parameter = urlencode({'p_anzahl': str(number), 'p_preis1': str(floor(price)), 'p_preis2': '{:02d}'.format(int(100*(price-floor(price)))),'p_id':'p'+str(item_id), 'prepare_markt':'true'}) 
        headers = {'User-Agent': USER_AGENT,\
            'Cookie': f'PHPSESSID={self.__session.session_id};wunr={self.__user_id}',\
                        'Connection': 'keep-alive'}
        response, content = self.__webclient.request(f'http://s{self.__session.server}{STATIC_DOMAIN}{MARKET_BOOTH_API}', \
                                                    'POST', \
                                                    parameter, \
                                                    headers)
        self.update_storage()
        self.__check_if_http_status_is_ok(response)
        parameter = urlencode({'p_anzahl': str(number), 'p_preis1': str(floor(price)), 'p_preis2': '{:02d}'.format(int(100*(price-floor(price)))),'p_id':str(item_id), 'verkaufe_markt':'OK'}) 
        response, _ = self.__webclient.request(f'http://s{self.__session.server}{STATIC_DOMAIN}{MARKET_BOOTH_API}', \
                                                    'POST', \
                                                    parameter, \
                                                    headers)
        self.update_storage()
        self.read_storage_from_server()

    def __get_to_market(self):
        headers = {'User-Agent': USER_AGENT,\
            'Cookie': f'PHPSESSID={self.__session.session_id};wunr={self.__user_id}',
            'Connection': 'Keep-Alive'}
        adresse= f'http://s{self.__session.server}{STATIC_DOMAIN}{MARKET_API}?page=1&order=&v='
        response, _ = self.__webclient.request(adresse, 'GET', headers = headers)
        adresse = f'http://s{self.__session.server}{STATIC_DOMAIN}{MARKET_BOOTH_API}'  
        response, _ = self.__webclient.request(adresse, 'GET', headers = headers)
        self.__check_if_http_status_is_ok(response)

    def __go_to_city(self):
        headers = {'Cookie': f'PHPSESSID={self.__session.session_id};wunr={self.__user_id}',
            'Connection': 'Keep-Alive'}
        adresse = f'http://s{self.__session.server}{STATIC_DOMAIN}/stadt/index.php?karte=1'
        
        response, _ = self.__webclient.request(adresse, 'GET', headers = headers)
        self.__check_if_http_status_is_ok(response)

    def __get_token_from_url(self, url):

        #token extrahieren
        split = re.search(r'https://.*/logw.php.*token=([a-f0-9]{32})', url)
        i_err = 0
        if split:
            tmp_token = split.group(1)
            if (tmp_token == ''):
                i_err = 1
        else:
            i_err = 1
            
        if (i_err == 1):
            self.__logger.debug(tmp_token)
            raise JSONError('Fehler bei der Ermittlung des Tokens')
        else:
            self.__token = tmp_token

    def __check_if_http_status_is_ok(self, response):
        """
        Prüft, ob der Status der HTTP Anfrage OK ist.
        """
        if not (response['status'] == str(HTTP_STATE_OK)):
            self.__logger.debug(f"HTTP State: {response['status']}")
            raise HTTPStateError('HTTP Status ist nicht OK')


    def __check_if_http_status_is_found(self, response):
        """
        Prüft, ob der Status der HTTP Anfrage FOUND ist.
        """
        if not (response['status'] == str(HTTP_STATE_FOUND)):
            self.__logger.debug(f"HTTP State: {response['status']}")
            raise HTTPStateError('HTTP Status ist nicht FOUND')

    def __check_if_session_is_deleted(self, cookie):
        """
        Prüft, ob die Session gelöscht wurde.
        """
        if not (cookie['PHPSESSID'].value == 'deleted'):
            self.__logger.debug(f"SessionID: {cookie['PHPSESSID'].value}")
            raise HTTPRequestError('Session was not deleted')

    def execute_command(self, command: str):
        headers = {'Cookie': 'PHPSESSID=' + self.__session.session_id + '; ' + \
                        'wunr=' + self.__user_id,
            'Connection': 'Keep-Alive'}
        adresse = f'http://s{self.__session.server}{STATIC_DOMAIN}{AJAX_PHP}{command}&token={self.__token}'
        
        try:
            response, content = self.__webclient.request(adresse, 'GET', headers = headers)
            self.__check_if_http_status_is_ok(response)
            jcontent = parsing_utils.generate_json_content_and_check_for_ok(content.decode('UTF-8'))
        except:
            raise
        else:
            return jcontent

    def execute_tree_gardencommand(self, command: str):
        headers = {'Cookie': f'PHPSESSID={self.__session.session_id};wunr={self.__user_id}',
            'Connection': 'Keep-Alive'}
        adresse = f'http://s{self.__session.server}{STATIC_DOMAIN}{TREE_QUEST_API}{command}'
        
        try:
            response, content = self.__webclient.request(adresse, 'GET', headers = headers)
            self.__check_if_http_status_is_ok(response)
            jcontent = parsing_utils.generate_json_content_and_check_for_status_success(content.decode('UTF-8'))
        except:
            raise
        else:
            return jcontent


    def execute_decogarden_command(self, command: str):
        headers = {'Cookie': f'PHPSESSID={self.__session.session_id};wunr={self.__user_id}',
            'Connection': 'Keep-Alive'}
        if(command != ""):
            deco_garden_api = DECO_GARDEN_API + '?'
        else:
            deco_garden_api = DECO_GARDEN_API
        adresse = f'http://s{self.__session.server}{STATIC_DOMAIN}{deco_garden_api}{command}'
        
        try:
            response, content = self.__webclient.request(adresse, 'GET', headers = headers)
            self.__check_if_http_status_is_ok(response)
            jcontent = parsing_utils.generate_json_content_and_check_for_ok(content.decode('UTF-8'))
        except:
            raise
        else:
            return jcontent

    def execute_wimp_command(self, command: str):
        headers = {'Cookie': f'PHPSESSID={self.__session.session_id};wunr={self.__user_id}',
            'Connection': 'Keep-Alive'}
        adresse = f'http://s{self.__session.server}{STATIC_DOMAIN}{WIMPS_API}{command}'
        try:
            response, content = self.__webclient.request(adresse, 'GET', headers = headers)
            self.__check_if_http_status_is_ok(response)
            jcontent = parsing_utils.generate_json_content_and_check_for_ok(content.decode('UTF-8'))
        except:
            raise
        else:
            return jcontent


    def destroy_weed_field(self, field_id: int):
        headers = {'Cookie': f'PHPSESSID={self.__session.session_id};wunr={self.__user_id}',
            'Connection': 'Keep-Alive'}
        adresse = f'http://s{self.__session.server}{STATIC_DOMAIN}{DESTROY_API}tile={field_id}'
        try:
            response, content = self.__webclient.request(adresse, 'GET', headers = headers)
            self.__check_if_http_status_is_ok(response)
            jcontent = parsing_utils.generate_json_content_and_check_for_success(content.decode('UTF-8'))
        except:
            raise

    def execute_message_command(self, message: message.Message):
        parameter = None
        headers = {'Cookie': f'PHPSESSID={self.__session.session_id};wunr={self.__user_id}',
            'Connection': 'Keep-Alive'}
        if(message is not None):
            parameter = urlencode({'hpc': message.id,
                    'msg_to': message.recipient,
                    'msg_subject': message.subject,
                    'msg_body': message.body,
                    'msg_send': 'senden'}) 
        adresse = f'http://s{self.__session.server()}{STATIC_DOMAIN}{MESSAGE_API}'
        try:
            if parameter is not None:
                response, content = self.__webclient.request(adresse, 'POST', parameter, headers)
            else: 
                response, content = self.__webclient.request(adresse, 'GET', headers=headers)
            self.__check_if_http_status_is_ok(response)
        except:
            raise
        else:
            return content

    def read_user_data_from_server(self):
        """
        Ruft eine Updatefunktion im Spiel auf und verarbeitet die empfangenen userdaten.
        """
        headers = {'Cookie': f'PHPSESSID={self.__session.session_id};wunr={self.__user_id}',
                   'Connection': 'Keep-Alive'}
        adresse = f'http://s{self.__session.server}.wurzelimperium.de/ajax/menu-update.php'

        response, content = self.__webclient.request(adresse, 'GET', headers = headers)
        self.__check_if_http_status_is_ok(response)
        #jcontent
        return parsing_utils.generate_json_content_and_check_for_success(content)
        

    def grow_plant(self, field, plant, garden_id, fields):
        headers = {'Cookie': f'PHPSESSID={self.__session.session_id};wunr={self.__user_id}',
                   'Connection': 'Keep-Alive'}
    
        adresse = f'http://s{self.__session.server}{STATIC_DOMAIN}{PLANT_API}?pflanze[]={plant}&feld[]={field}&felder[]={fields}&cid={self.__token}&garden={garden_id}'

        try:
            response, content = self.__webclient.request(adresse, 'GET', headers = headers)
        except:
            raise
        else:
            pass

    def water_plant(self, garden_id, field_id, fields_to_water):
        headers = {'User-Agent': USER_AGENT,\
                   'Cookie': f'PHPSESSID={self.__session.session_id};wunr={self.__user_id}',\
                   'X-Requested-With': 'XMLHttpRequest',\
                   'Connection': 'Keep-Alive'}
        adresse = f'http://s{self.__session.server}{STATIC_DOMAIN}{WATER_API}?feld[]={field_id}&felder[]={fields_to_water}&cid={self.__token}&garden={garden_id}'

        try:
            response, content = self.__webclient.request(adresse, 'GET', headers = headers)
            self.__check_if_http_status_is_ok(response)
            parsing_utils.generate_yaml_content_and_check_for_success(content.decode('UTF-8'))
        except:
            raise

    def get_username_from_server(self):
        headers = {'Cookie': 'PHPSESSID=' + self.__session.session_id + '; ' + \
                             'wunr=' + self.__user_id, \
                   'Connection': 'Keep-Alive', \
                   'Referer':f'PHPSESSID={self.__session.session_id};wunr={self.__user_id}', \
                   'X-Requested-With':'X-Requested-With: XMLHttpRequest'}
        adresse = f'http://s{self.__session.server}{STATIC_DOMAIN}{AJAX_PHP}do=statsGetStats&which=0&start=0&additional={self.__user_id}&token={self.__token}'
        
        try:
            response, content = self.__webclient.request(adresse, 'GET', headers = headers)
            self.__check_if_http_status_is_ok(response)
            jContent = parsing_utils.generate_json_content_and_check_for_ok(content)
            userName = parsing_utils.get_username_from_json_content(jContent)
        except:
            raise
        else:
            return userName


    def get_trophies(self):
        """
        Funktion ermittelt, ob die Imkerei verfügbar ist und gibt True/False zurück.
        Dazu muss ein Mindestlevel von 10 erreicht sein und diese dann freigeschaltet sein.
        Die Freischaltung wird anhand eines Geschenks im Spiel geprüft.
        """

        headers = {'Cookie': f'PHPSESSID={self.__session.session_id};wunr={self.__user_id}',
                   'Connection': 'Keep-Alive'}
        adresse = f'http://s{self.__session.server}{STATIC_DOMAIN}/ajax/gettrophies.php?category=giver'
        

        response, content = self.__webclient.request(adresse, 'GET', headers = headers)
        self.__check_if_http_status_is_ok(response)
        return parsing_utils.generate_json_content_and_check_for_ok(content)

    def get_user_profile(self):
        """
        Prüft, ob die E-Mail Adresse im Profil bestätigt ist.
        """
        headers = {'User-Agent': USER_AGENT,\
                   'Cookie': f'PHPSESSID={self.__session.session_id};wunr={self.__user_id}'}

        adresse = f'http://s{self.__session.server}{STATIC_DOMAIN}/nutzer/profil.php'

        response, content = self.__webclient.request(adresse, 'GET', headers = headers)
        self.__check_if_http_status_is_ok(response)
        return content.decode('utf-8')

    def read_storage_from_server(self):

        headers = {'User-Agent': USER_AGENT,\
                   'Cookie': f'PHPSESSID={self.__session.session_id};wunr={self.__user_id}'}

        adress = f'http://s{self.__session.server}{STATIC_DOMAIN}/ajax/updatelager.php?all=1'

        try:
            response, content = self.__webclient.request(adress, 'GET', headers = headers)
            self.__check_if_http_status_is_ok(response)
            jContent = parsing_utils.generate_json_content_and_check_for_ok(content)
        except:
            raise
        else:
            return jContent['produkte']

    def update_storage(self):
        headers = {'User-Agent': USER_AGENT,\
                   'Cookie': f'PHPSESSID={self.__session.session_id};wunr={self.__user_id}'}

        adress = f'http://s{self.__session.server}{STATIC_DOMAIN}/ajax/updatelager.php'
        parameter = urlencode({'all': '1',
                    'sort': '1',
                    'type': 'normal',
                    'token': self.__token})
        try:
            response, content = self.__webclient.request(adress, \
                                        'POST', \
                                        parameter, \
                                        headers)
            content = parsing_utils.generate_json_content_and_check_for_ok(content)
        except:
            raise




    def get_all_product_informations(self):
        """
        Sammelt alle Produktinformationen und gibt diese zur Weiterverarbeitung zurück.
        """

        headers = {'Cookie': f'PHPSESSID={self.__session.session_id};wunr={self.__user_id}'}

        adresse = f'http://s{self.__session.server}{STATIC_DOMAIN}/main.php?page=garden'
        response, content = self.__webclient.request(adresse, 'GET', headers = headers)
        content = content.decode('UTF-8')
        self.__check_if_http_status_is_ok(response)
        reToken = re.search(r'ajax\.setToken\(\"(.*)\"\);', content)
        self.__token = reToken.group(1) #TODO: except, wenn token nicht aktualisiert werden kann
        return content

    def get_all_tradeable_products(self):
        """
        Gibt eine Liste zurück, welche Produkte handelbar sind.
        """
        
        headers = {'Cookie': f'PHPSESSID={self.__session.session_id};wunr={self.__user_id}',
                    'Content-Length':'0'}

        adresse = f'http://s{self.__session.server}{STATIC_DOMAIN}/stadt/markt.php?show=overview'
        
        response, content = self.__webclient.request(adresse, 'GET', headers = headers)
        self.__check_if_http_status_is_ok(response)
        return content

    

    def get_offers_from_product(self, id):
        """
        Gibt eine Liste mit allen Angeboten eines Produkts zurück.
        """
        
        headers = {'Cookie': f'PHPSESSID={self.__session.session_id};wunr={self.__user_id}',
                    'Content-Length':'0'}

        nextPage = True
        iPage = 1
        while (nextPage):
            
            nextPage = False
            adresse = f'http://s{self.__session.server}{STATIC_DOMAIN}/stadt/markt.php?order=p&v={id}&filter=1&page={iPage}'
            
            try:
                response, content = self.__webclient.request(adresse, 'GET', headers = headers)
                self.__check_if_http_status_is_ok(response)
            except:
                pass #TODO: exception definieren
            else:
                html_file = io.BytesIO(content)
                html_tree = html.parse(html_file)
                root = html_tree.getroot()
                table = root.findall('./body/div/table/*')
                
                if (table[1][0].text == 'Keine Angebote'):
                    pass
                else:
                    #range von 1 bis länge-1, da erste Zeile Überschriften sind und die letzte Weiter/Zurück.
                    #Falls es mehrere seiten gibt.
                    list_offers = self.__get_amounts_and_prices_from_table(table)

                    for element in table[len(table)-1][0]:
                        if 'weiter' in element.text:
                            nextPage = True
                            iPage = iPage + 1

        return list_offers 

    def __get_amounts_and_prices_from_table(self, table):
        list_offers = []
        for i in range(1, len(table)-1):
            anzahl = table[i][0].text
            anzahl = anzahl.encode('utf-8')
            anzahl = anzahl.replace('.', '')
                        
            preis = table[i][3].text
            preis = preis.encode('utf-8')
            preis = preis.replace('\xc2\xa0wT', '')
            preis = preis.replace('.', '')
            preis = preis.replace(',', '.')
                        #produkt = table[i][1][0].text
                        #verkaeufer = table[i][2][0].text
        
            list_offers.append([int(anzahl), float(preis)]) 
        return list_offers

    def get_npc_prices(self):
        """
        Ermittelt aus der Wurzelimperium-Hilfe die NPC Preise aller Produkte.
        """

        headers = {'Cookie': f'PHPSESSID={self.__session.session_id};wunr={self.__user_id}',
                    'Content-Length':'0'}

        adresse = f'http://s{self.__session.server}{STATIC_DOMAIN}/hilfe.php?item=2'

        #try:
        response, content = self.__webclient.request(adresse, 'GET', headers = headers)
        self.__check_if_http_status_is_ok(response)
        
        content = content.decode('UTF-8').replace('Gärten & Regale', 'Gärten und Regale')
        content = bytearray(content, encoding='UTF-8')

        dictNPCPrices = parsing_utils.parse_npc_prices_from_html(content)
        #except:
        #    pass #TODO Exception definieren
        #else:
        return dictNPCPrices

    def __check_if_http_status_is_ok(self, response):
        if not (response['status'] == str(HTTP_STATE_OK)):
            raise HTTPStateError('HTTP Status is not ok')

    def get_notes(self):
        """
        get the users note
        """

        headers = {'Cookie': f'PHPSESSID={self.__session.session_id};wunr={self.__user_id}',
                    'Content-Length':'0'}

        adresse = f'http://s{self.__session.server}{STATIC_DOMAIN}{NOTES_API}'
        try:
            response, content = self.__webclient.request(adresse, 'POST', headers = headers)
            self.__check_if_http_status_is_ok(response)
            content = content.decode('UTF-8')
            my_parser = etree.HTMLParser(recover=True)
            html_tree = etree.fromstring(content, parser=my_parser)

            note = html_tree.find('./body/form/div/textarea[@id="notiztext"]')
            return note.text.strip()
        except:
            raise





class HTTPStateError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class JSONError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    
class HTTPRequestError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


