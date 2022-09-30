from os import ST_APPEND
from urllib.parse import urlencode
import json, re, httplib2
from http.cookies import SimpleCookie
from . import session
import yaml, time, logging, math, io
import xml.etree.ElementTree as eTree
from lxml import html
from . import login_data
from . import message

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
DECO_GARDEN_API                = '/ajax/decogardenajax.php?'

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
        self.__logger.setLevel(logging.DEBUG)
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
            jcontent = self.__generate_json_content_and_check_for_ok(content)
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
        headers = {'Cookie': 'PHPSESSID=' + self.__session.session_id + '; ' + 'wunr=' + self.__user_id}
        
        adresse = 'http://s'+str(self.__session.server) +  STATIC_DOMAIN +'/main.php?page=logout'

        try: #content ist beim Logout leer
            response, content = self.__webclient.request(adresse, 'GET', headers=headers)
            self.__check_if_http_status_is_found(response)
            cookie = SimpleCookie(response['set-cookie'])
            self.__check_if_session_is_deleted(cookie)
        except:
            raise
        else:
            self.__del__()



    def __check_if_http_status_is_ok(self, response):
        if not (response['status'] == str(HTTP_STATE_OK)):
            self.__logger.debug('HTTP State: ' + str(response['status']))
            raise HTTPStateError('HTTP Status is not ok')


    def __generate_json_content_and_check_for_success(self, content):
        """
        Aufbereitung und Prüfung der vom Server empfangenen JSON Daten.
        """
        jContent = json.loads(content)
        if (jContent['success'] == 1): return jContent
        else: raise JSONError


    def __generate_json_content_and_check_for_ok(self, content : str):
        """
        Aufbereitung und Prüfung der vom Server empfangenen JSON Daten.
        """
        jContent = json.loads(content)
        if (jContent['status'] == 'ok'): return jContent
        else: raise JSONError('JSON not ok')

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
            raise JSONError('Fehler bei der Ermittlung des tokens')
        else:
            self.__token = tmp_token

    def __check_if_http_status_is_ok(self, response):
        """
        Prüft, ob der Status der HTTP Anfrage OK ist.
        """
        if not (response['status'] == str(HTTP_STATE_OK)):
            self.__logger.debug('HTTP State: ' + str(response['status']))
            raise HTTPStateError('HTTP Status ist nicht OK')


    def __check_if_http_status_is_found(self, response):
        """
        Prüft, ob der Status der HTTP Anfrage FOUND ist.
        """
        if not (response['status'] == str(HTTP_STATE_FOUND)):
            self.__logger.debug('HTTP State: ' + str(response['status']))
            raise HTTPStateError('HTTP Status ist nicht FOUND')

    def __check_if_session_is_deleted(self, cookie):
        """
        Prüft, ob die Session gelöscht wurde.
        """
        if not (cookie['PHPSESSID'].value == 'deleted'):
            self.__logger.debug('SessionID: ' + cookie['PHPSESSID'].value)
            raise HTTPRequestError('Session was not deleted')

    def execute_command(self, command: str):
        headers = {'Cookie': 'PHPSESSID=' + self.__session.session_id + '; ' + \
                        'wunr=' + self.__user_id,
            'Connection': 'Keep-Alive'}
        adresse = 'http://s' + str(self.__session.server) + STATIC_DOMAIN + AJAX_PHP +command+ '&token=' + self.__token
        
        try:
            response, content = self.__webclient.request(adresse, 'GET', headers = headers)
            self.__check_if_http_status_is_ok(response)
            jcontent = self.__generate_json_content_and_check_for_ok(content.decode('UTF-8'))
        except:
            raise
        else:
            return jcontent

    def execute_decogarden_command(self, command: str):
        headers = {'Cookie': 'PHPSESSID=' + self.__session.session_id + '; ' + \
                        'wunr=' + self.__user_id,
            'Connection': 'Keep-Alive'}
        adresse = 'http://s' + str(self.__session.server) + STATIC_DOMAIN + DECO_GARDEN_API +command
        
        try:
            response, content = self.__webclient.request(adresse, 'GET', headers = headers)
            self.__check_if_http_status_is_ok(response)
            jcontent = self.__generate_json_content_and_check_for_ok(content.decode('UTF-8'))
        except:
            raise
        else:
            return jcontent

    def execute_message_command(self, message: message.Message):
        parameter = None
        headers = {'Cookie': 'PHPSESSID=' + self.__session.session_id + '; ' + \
                        'wunr=' + self.__user_id,
            'Connection': 'Keep-Alive'}
        if(message is not None):
            parameter = urlencode({'hpc': message.id,
                    'msg_to': message.recipient,
                    'msg_subject': message.subject,
                    'msg_body': message.body,
                    'msg_send': 'senden'}) 
        adresse = 'http://s' + str(self.__session.server()) + STATIC_DOMAIN + MESSAGE_API        
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
        headers = {'Cookie': 'PHPSESSID=' + self.__session.session_id + '; ' + \
                             'wunr=' + self.__user_id,
                   'Connection': 'Keep-Alive'}
        adresse = 'http://s' + str(self.__session.server) + '.wurzelimperium.de/ajax/menu-update.php'

        response, content = self.__webclient.request(adresse, 'GET', headers = headers)
        self.__check_if_http_status_is_ok(response)
        #jcontent
        return self.__generate_json_content_and_check_for_success(content)
        

    def grow_plant(self, field, plant, garden_id, fields):
        headers = {'Cookie': 'PHPSESSID=' + self.__session.session_id + '; ' + \
                             'wunr=' + self.__user_id,
                   'Connection': 'Keep-Alive'}
    
        adresse = 'http://s' + str(self.__session.server) + \
                  STATIC_DOMAIN + PLANT_API + '?pflanze[]=' + str(plant) + \
                  '&feld[]=' + str(field) + \
                  '&felder[]=' + fields + \
                  '&cid=' + self.__token + \
                  '&garden=' + str(garden_id)

        try:
            response, content = self.__webclient.request(adresse, 'GET', headers = headers)
        except:
            print('except')
            raise
        else:
            pass

    def water_plant(self, garden_id, field_id, fields_to_water):
        headers = {'User-Agent': USER_AGENT,\
                   'Cookie': 'PHPSESSID=' + self.__session.session_id + '; ' + \
                             'wunr=' + self.__user_id,\
                   'X-Requested-With': 'XMLHttpRequest',\
                   'Connection': 'Keep-Alive'}
        adresse = 'http://s' + str(self.__session.server) + STATIC_DOMAIN + WATER_API + '?feld[]=' + \
                  str(field_id) + '&felder[]=' + fields_to_water + '&cid=' + self.__token + '&garden=' + str(garden_id)

        try:
            response, content = self.__webclient.request(adresse, 'GET', headers = headers)
            self.__check_if_http_status_is_ok(response)
            self.__generate_yaml_content_and_check_for_success(content.decode('UTF-8'))
        except:
            raise

    def get_username_from_server(self):
        headers = {'Cookie': 'PHPSESSID=' + self.__session.session_id + '; ' + \
                             'wunr=' + self.__user_id, \
                   'Connection': 'Keep-Alive', \
                   'Referer':'http://s' + str(self.__session.server)+ STATIC_DOMAIN + '/main.php?page=garden', \
                   'X-Requested-With':'X-Requested-With: XMLHttpRequest'}
        adresse = 'http://s' + str(self.__session.server) + STATIC_DOMAIN + AJAX_PHP + 'do=statsGetStats&which=0&start=0&additional='+\
                  self.__user_id + '&token=' + self.__token
        
        try:
            response, content = self.__webclient.request(adresse, 'GET', headers = headers)
            self.__check_if_http_status_is_ok(response)
            jContent = self.__generate_json_content_and_check_for_ok(content)
            userName = self.__get_username_from_json_content(jContent)
        except:
            raise
        else:
            return userName

    def __get_username_from_json_content(self, jContent):
        """
        Sucht im übergebenen JSON Objekt nach dem Usernamen und gibt diesen zurück.
        """
        result = False
        for i in range(0, len(jContent['table'])):
            sUserName = str(jContent['table'][i])  
            if 'Spielername' in sUserName:
                sUserName = sUserName.replace('<tr>', '')
                sUserName = sUserName.replace('<td>', '')
                sUserName = sUserName.replace('</tr>', '')
                sUserName = sUserName.replace('</td>', '')
                sUserName = sUserName.replace('Spielername', '')
                sUserName = sUserName.replace('&nbsp;', '')
                sUserName = sUserName.strip()
                result = True
                break
        if result:
            return sUserName
        else:
            self.__logger.debug(jContent['table'])
            raise JSONError('Spielername nicht gefunden.')

    def __generate_yaml_content_and_check_for_success(self, content : str):
        """
        Aufbereitung und Prüfung der vom Server empfangenen YAML Daten auf Erfolg.
        """
        content = content.replace('\n', ' ')
        content = content.replace('\t', ' ')
        yContent = yaml.load(content, Loader=yaml.FullLoader)
        
        if (yContent['success'] != 1):
            raise YAMLError("YAML Error")


    def __generate_yaml_content_and_check_status_for_ok(self, content):
        """
        Aufbereitung und Prüfung der vom Server empfangenen YAML Daten auf iO Status.
        """
        content = content.replace('\n', ' ')
        content = content.replace('\t', ' ')
        yContent = yaml.load(content, Loader=yaml.FullLoader)
        
        if (yContent['status'] != 'ok'):
            raise YAMLError("YAMLError")

    def get_trophies(self):
        """
        Funktion ermittelt, ob die Imkerei verfügbar ist und gibt True/False zurück.
        Dazu muss ein Mindestlevel von 10 erreicht sein und diese dann freigeschaltet sein.
        Die Freischaltung wird anhand eines Geschenks im Spiel geprüft.
        """

        headers = {'Cookie': 'PHPSESSID=' + self.__session.session_id + '; ' + \
                             'wunr=' + self.__user_id,
                   'Connection': 'Keep-Alive'}
        adresse = 'http://s' + str(self.__session.server) + \
                  + STATIC_DOMAIN + '/ajax/gettrophies.php?category=giver'
        

        response, content = self.__webclient.request(adresse, 'GET', headers = headers)
        self.__check_if_http_status_is_ok(response)
        return self.__generate_json_content_and_check_for_ok(content)

    def get_user_profile(self):
        """
        Prüft, ob die E-Mail Adresse im Profil bestätigt ist.
        """
        headers = {'User-Agent': USER_AGENT,\
                   'Cookie': 'PHPSESSID=' + self.__session.session_id + '; ' + \
                             'wunr=' + self.__user_id}

        adresse = 'http://s' + str(self.__session.server) + STATIC_DOMAIN + '/nutzer/profil.php'

        response, content = self.__webclient.request(adresse, 'GET', headers = headers)
        self.__check_if_http_status_is_ok(response)
        return content

    def read_storage_from_server(self):

        headers = {'User-Agent': USER_AGENT,\
                   'Cookie': 'PHPSESSID=' + self.__session.session_id + '; ' + \
                             'wunr=' + self.__user_id}

        adress = 'http://s' + str(self.__session.server) + STATIC_DOMAIN +'/ajax/updatelager.' + \
                 'php?all=1'

        try:
            response, content = self.__webclient.request(adress, 'GET', headers = headers)
            self.__check_if_http_status_is_ok(response)
            jContent = self.__generate_json_content_and_check_for_ok(content)
        except:
            raise
        else:
            return jContent['produkte']

    def get_all_product_informations(self):
        """
        Sammelt alle Produktinformationen und gibt diese zur Weiterverarbeitung zurück.
        """

        headers = {'Cookie': 'PHPSESSID=' + self.__session.session_id + '; ' + \
                             'wunr=' + self.__user_id}

        adresse = 'http://s' + str(self.__session.server) + STATIC_DOMAIN + '/main.php?page=garden'
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
        
        headers = {'Cookie': 'PHPSESSID=' + self.__session.session_id + '; ' + \
                             'wunr=' + self.__user_id,
                    'Content-Length':'0'}

        adresse = 'http://s' + str(self.__session.server) + STATIC_DOMAIN + '/stadt/markt.php?show=overview'
        
        response, content = self.__webclient.request(adresse, 'GET', headers = headers)
        self.__check_if_http_status_is_ok(response)
        return content

    def get_offers_from_product(self, id):
        """
        Gibt eine Liste mit allen Angeboten eines Produkts zurück.
        """
        
        headers = {'Cookie': 'PHPSESSID=' + self.__session.session_id + '; ' + \
                             'wunr=' + self.__user_id,
                    'Content-Length':'0'}

        nextPage = True
        iPage = 1
        listOffers = []
        while (nextPage):
            
            nextPage = False
            adresse = 'http://s' + str(self.__session.server) + STATIC_DOMAIN + '/stadt/markt.php?order=p&v='+ str(id) +'&filter=1&page='+str(iPage)
            
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
        
                        listOffers.append([int(anzahl), float(preis)])

                    for element in table[len(table)-1][0]:
                        if 'weiter' in element.text:
                            nextPage = True
                            iPage = iPage + 1

        return listOffers  

    def get_npc_prices(self):
        """
        Ermittelt aus der Wurzelimperium-Hilfe die NPC Preise aller Produkte.
        """

        headers = {'Cookie': 'PHPSESSID=' + self.__session.session_id + '; ' + \
                             'wunr=' + self.__user_id,
                    'Content-Length':'0'}

        adresse = 'http://s' + str(self.__session.server) +STATIC_DOMAIN +'/hilfe.php?item=2'

        #try:
        response, content = self.__webclient.request(adresse, 'GET', headers = headers)
        self.__check_if_http_status_is_ok(response)
        
        content = content.decode('UTF-8').replace('Gärten & Regale', 'Gärten und Regale')
        content = bytearray(content, encoding='UTF-8')

        dictNPCPrices = self.__parse_npc_prices_from_html(content)
        #except:
        #    pass #TODO Exception definieren
        #else:
        return dictNPCPrices

    def __parse_npc_prices_from_html(self, html):
            """
            Parsen aller NPC Preise aus dem HTML Skript der Spielehilfe.
            """
            #ElementTree benötigt eine Datei zum Parsen.
            #Mit BytesIO wird eine Datei im Speicher angelegt, nicht auf der Festplatte.
            html_file = io.BytesIO(html)
            
            html_tree = eTree.parse(html_file)
            root = html_tree.getroot()
            table = root.find('./body/div[@id="content"]/table')
            
            dictResult = {}
            
            for row in table.iter('tr'):
                
                produktname = row[0].text
                npc_preis = row[1].text
                
                #Bei der Tabellenüberschrift ist der Text None
                if produktname != None and npc_preis != None:
                    # NPC-Preis aufbereiten
                    npc_preis = str(npc_preis)
                    npc_preis = npc_preis.replace(' wT', '')
                    npc_preis = npc_preis.replace('.', '')
                    npc_preis = npc_preis.replace(',', '.')
                    npc_preis = npc_preis.strip()
                    if '-' in npc_preis:
                        npc_preis = None
                    else:
                        npc_preis = float(npc_preis)
                        
                    dictResult[produktname] = npc_preis
                    
            return dictResult

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

class YAMLError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
