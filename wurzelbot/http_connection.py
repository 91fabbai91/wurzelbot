import logging
import re
from http import HTTPStatus
from http.cookies import SimpleCookie
from math import floor
from urllib.parse import urlencode

import httplib2
import login_data
import message
import parsing_utils
import session
from parsing_utils import HTTPStateError, JSONError

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36"
    + "(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36 Vivaldi/2.2.1388.37"
)
STATIC_DOMAIN = ".wurzelimperium.de"
AJAX_PHP = "/ajax/ajax.php?"
MESSAGE_API = "/nachrichten"
WATER_API = "/save/wasser.php"
PLANT_API = "/save/pflanz.php"
DECO_GARDEN_API = "/ajax/decogardenajax.php"
DESTROY_API = "/save/abriss.php?"
MARKET_BOOTH_API = "/stadt/marktstand.php"
MARKET_API = "/stadt/markt.php"
TREE_QUEST_API = "/treequestquery.php?"
WIMPS_API = "/ajax/verkaufajax.php?"
NOTES_API = "/notiz.php"


class HTTPRequestError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class HTTPConnection:
    # singleton for just one login, due to the backend
    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(HTTPConnection, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.__webclient = httplib2.Http(disable_ssl_certificate_validation=True)
        self.__webclient.follow_redirects = False
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__session = session.Session()
        self.__token = None
        self.__user_id = None

    def __del__(self):
        self.__session = None
        self.__token = None
        self.__user_id = None

    @property
    def user_id(self):
        return self.__user_id

    def login(self, login_data: login_data.LoginData):
        parameter = urlencode(
            {
                "do": "login",
                "server": "server" + str(login_data.server),
                "user": login_data.username,
                "pass": login_data.password.get_secret_value(),
            }
        )

        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            "Connection": "keep-alive",
        }

        response, content = self.__webclient.request(
            "https://www.wurzelimperium.de/dispatch.php", "POST", parameter, headers
        )

        check_if_http_status_is_ok(response)
        jcontent = parsing_utils.generate_json_content_and_check_for_ok(content)
        self.__get_token_from_url(jcontent["url"])
        url = jcontent["url"]
        response, content = self.__webclient.request(url, "GET", headers=headers)
        self.__check_if_http_status_is_found(response)
        cookie = SimpleCookie(response["set-cookie"])
        cookie.load(str(response["set-cookie"]).replace("secure, ", "", -1))
        self.__session.open_session(cookie["PHPSESSID"].value, str(login_data.server))
        self.__user_id = cookie["wunr"].value

    def logout(self):
        headers = {
            "Cookie": f"PHPSESSID={self.__session.session_id};wunr={self.__user_id}"
        }

        adresse = f"http://s{self.__session.server}{STATIC_DOMAIN}/main.php?page=logout"

        response, _ = self.__webclient.request(adresse, "GET", headers=headers)
        self.__check_if_http_status_is_found(response)
        cookie = SimpleCookie(response["set-cookie"])
        self.__check_if_session_is_deleted(cookie)
        del self

    def sell_on_market(self, item_id: int, price: float, number: int):
        self.execute_command("do=citymap_init")
        self.__go_to_city()
        self.__get_to_market()
        parameter = urlencode(
            {
                "p_anzahl": str(number),
                "p_preis1": str(floor(price)),
                "p_preis2": "{:02d}".format(int(100 * (price - floor(price)))),
                "p_id": "p" + str(item_id),
                "prepare_markt": "true",
            }
        )
        headers = {
            "User-Agent": USER_AGENT,
            "Cookie": f"PHPSESSID={self.__session.session_id};wunr={self.__user_id}",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "text/html,application/xhtml+xml,application/xml"
            + ";q=0.9,image/avif,image/webp,*/*;q=0.8",
        }
        response, _ = self.__webclient.request(
            f"http://s{self.__session.server}{STATIC_DOMAIN}{MARKET_BOOTH_API}",
            method="POST",
            body=parameter,
            headers=headers,
        )
        self.update_storage()
        check_if_http_status_is_ok(response)
        parameter = urlencode(
            {
                "p_anzahl": str(number),
                "p_preis1": str(floor(price)),
                "p_preis2": "{:02d}".format(int(100 * (price - floor(price)))),
                "p_id": str(item_id),
                "verkaufe_markt": "OK",
            }
        )
        response, _ = self.__webclient.request(
            f"http://s{self.__session.server}{STATIC_DOMAIN}{MARKET_BOOTH_API}",
            "POST",
            parameter,
            headers,
        )
        self.update_storage()
        self.read_storage_from_server()

    def __get_to_market(self):
        headers = {
            "User-Agent": USER_AGENT,
            "Cookie": f"PHPSESSID={self.__session.session_id};wunr={self.__user_id}",
            "Connection": "Keep-Alive",
        }
        adresse = f"http://s{self.__session.server}{STATIC_DOMAIN}{MARKET_API}?page=1&order=&v="
        response, _ = self.__webclient.request(adresse, "GET", headers=headers)
        check_if_http_status_is_ok(response)
        adresse = f"http://s{self.__session.server}{STATIC_DOMAIN}{MARKET_BOOTH_API}"
        response, _ = self.__webclient.request(adresse, "GET", headers=headers)
        check_if_http_status_is_ok(response)

    def __go_to_city(self):
        headers = {
            "Cookie": f"PHPSESSID={self.__session.session_id};wunr={self.__user_id}",
            "Connection": "Keep-Alive",
        }
        adresse = (
            f"http://s{self.__session.server}{STATIC_DOMAIN}/stadt/index.php?karte=1"
        )

        response, _ = self.__webclient.request(adresse, "GET", headers=headers)
        check_if_http_status_is_ok(response)

    def __get_token_from_url(self, url):
        # token extrahieren
        split = re.search(r"https://.*/logw.php.*token=([a-f0-9]{32})", url)
        i_err = 0
        if split:
            tmp_token = split.group(1)
            if tmp_token == "":
                i_err = 1
        else:
            i_err = 1

        if i_err == 1:
            self.__logger.debug(tmp_token)
            raise JSONError("Fehler bei der Ermittlung des Tokens")

        self.__token = tmp_token

    def __check_if_http_status_is_ok(self, response):
        """
        Prüft, ob der Status der HTTP Anfrage OK ist.
        """
        if not response["status"] == str(HTTPStatus.OK.value):
            self.__logger.debug(f"HTTP State: {response['status']}")
            raise HTTPStateError("HTTP Status ist nicht OK")

    def __check_if_http_status_is_found(self, response):
        """
        Prüft, ob der Status der HTTP Anfrage FOUND ist.
        """
        if not response["status"] == str(HTTPStatus.FOUND.value):
            self.__logger.debug(f"HTTP State: {response['status']}")
            raise HTTPStateError("HTTP Status ist nicht FOUND")

    def __check_if_session_is_deleted(self, cookie):
        """
        Prüft, ob die Session gelöscht wurde.
        """
        if not cookie["PHPSESSID"].value == "deleted":
            self.__logger.debug(f"SessionID: {cookie['PHPSESSID'].value}")
            raise HTTPRequestError("Session was not deleted")

    def execute_command(self, command: str):
        headers = {
            "Cookie": "PHPSESSID="
            + self.__session.session_id
            + "; "
            + "wunr="
            + self.__user_id,
            "Connection": "Keep-Alive",
        }
        adresse = (
            f"http://s{self.__session.server}{STATIC_DOMAIN}{AJAX_PHP}"
            + f"{command}&token={self.__token}"
        )

        response, content = self.__webclient.request(adresse, "GET", headers=headers)
        check_if_http_status_is_ok(response)
        jcontent = parsing_utils.generate_json_content_and_check_for_ok(
            content.decode("UTF-8")
        )
        return jcontent

    def execute_tree_gardencommand(self, command: str):
        headers = {
            "Cookie": f"PHPSESSID={self.__session.session_id};wunr={self.__user_id}",
            "Connection": "Keep-Alive",
        }
        adresse = (
            f"http://s{self.__session.server}{STATIC_DOMAIN}{TREE_QUEST_API}{command}"
        )

        response, content = self.__webclient.request(adresse, "GET", headers=headers)
        check_if_http_status_is_ok(response)
        jcontent = parsing_utils.generate_json_content_and_check_for_status_success(
            content.decode("UTF-8")
        )
        return jcontent

    def execute_decogarden_command(self, command: str):
        headers = {
            "Cookie": f"PHPSESSID={self.__session.session_id};wunr={self.__user_id}",
            "Connection": "Keep-Alive",
        }
        if command != "":
            deco_garden_api = DECO_GARDEN_API + "?"
        else:
            deco_garden_api = DECO_GARDEN_API
        adresse = (
            f"http://s{self.__session.server}{STATIC_DOMAIN}{deco_garden_api}{command}"
        )
        response, content = self.__webclient.request(adresse, "GET", headers=headers)
        check_if_http_status_is_ok(response)
        jcontent = parsing_utils.generate_json_content_and_check_for_ok(
            content.decode("UTF-8")
        )
        return jcontent

    def execute_wimp_command(self, command: str):
        headers = {
            "Cookie": f"PHPSESSID={self.__session.session_id};wunr={self.__user_id}",
            "Connection": "Keep-Alive",
        }
        adresse = f"http://s{self.__session.server}{STATIC_DOMAIN}{WIMPS_API}{command}"
        response, content = self.__webclient.request(adresse, "GET", headers=headers)
        check_if_http_status_is_ok(response)
        jcontent = parsing_utils.generate_json_content_and_check_for_ok(
            content.decode("UTF-8")
        )
        return jcontent

    def execute_market_command(self, identifier: int, page: int = 1) -> str:
        headers = {
            "Cookie": f"PHPSESSID={self.__session.session_id};"
            + f"wunr={self.__user_id}",
            "Content-Length": "0",
        }
        adresse = (
            f"http://s{self.__session.server}{STATIC_DOMAIN}"
            + f"{MARKET_API}?order=p&v={identifier}&filter=1&page={page}"
        )

        response, content = self.__webclient.request(adresse, "GET", headers=headers)
        check_if_http_status_is_ok(response)
        return content.decode("UTF-8")

    def destroy_weed_field(self, field_id: int):
        headers = {
            "Cookie": f"PHPSESSID={self.__session.session_id};wunr={self.__user_id}",
            "Connection": "Keep-Alive",
        }
        adresse = f"http://s{self.__session.server}{STATIC_DOMAIN}{DESTROY_API}tile={field_id}"
        response, content = self.__webclient.request(adresse, "GET", headers=headers)
        check_if_http_status_is_ok(response)
        jcontent = parsing_utils.generate_json_content_and_check_for_success(
            content.decode("UTF-8")
        )
        return jcontent

    def execute_message_command(
        self, url_extension: str, message: message.Message = None
    ) -> str:
        parameter = None
        headers = {
            "Cookie": f"PHPSESSID={self.__session.session_id};wunr={self.__user_id}",
            "Connection": "Keep-Alive",
        }
        if message is not None:
            parameter = urlencode(
                {
                    "hpc": message.id,
                    "msg_to": message.recipient,
                    "msg_subject": message.subject,
                    "msg_body": message.body,
                    "msg_send": "senden",
                }
            )
        adresse = f"http://s{self.__session.server()}{STATIC_DOMAIN}{MESSAGE_API}/{url_extension}"

        if parameter is not None:
            response, content = self.__webclient.request(
                adresse, "POST", parameter, headers
            )
        else:
            response, content = self.__webclient.request(
                adresse, "GET", headers=headers
            )
        check_if_http_status_is_ok(response)

        return content

    def read_user_data_from_server(self):
        """
        Ruft eine Updatefunktion im Spiel auf und verarbeitet die empfangenen userdaten.
        """
        headers = {
            "Cookie": f"PHPSESSID={self.__session.session_id};wunr={self.__user_id}",
            "Connection": "Keep-Alive",
        }
        adresse = (
            f"http://s{self.__session.server}.wurzelimperium.de/ajax/menu-update.php"
        )

        response, content = self.__webclient.request(adresse, "GET", headers=headers)
        check_if_http_status_is_ok(response)
        # jcontent
        return parsing_utils.generate_json_content_and_check_for_success(content)

    def grow_plant(self, field, plant, garden_id, fields):
        headers = {
            "Cookie": f"PHPSESSID={self.__session.session_id};wunr={self.__user_id}",
            "Connection": "Keep-Alive",
        }

        address = (
            f"http://s{self.__session.server}{STATIC_DOMAIN}{PLANT_API}"
            + f"?pflanze[]={plant}&feld[]={field}&felder[]={fields}&cid={self.__token}&garden={garden_id}"
        )

        self.__webclient.request(address, "GET", headers=headers)

    def water_plant(self, garden_id, field_id, fields_to_water):
        headers = {
            "User-Agent": USER_AGENT,
            "Cookie": f"PHPSESSID={self.__session.session_id};wunr={self.__user_id}",
            "X-Requested-With": "XMLHttpRequest",
            "Connection": "Keep-Alive",
        }
        address = (
            f"http://s{self.__session.server}{STATIC_DOMAIN}{WATER_API}"
            + f"?feld[]={field_id}&felder[]={fields_to_water}&cid={self.__token}&garden={garden_id}"
        )
        response, content = self.__webclient.request(address, "GET", headers=headers)
        check_if_http_status_is_ok(response)
        parsing_utils.generate_yaml_content_and_check_for_success(
            content.decode("UTF-8")
        )

    def get_username_from_server(self):
        headers = {
            "Cookie": "PHPSESSID="
            + self.__session.session_id
            + "; "
            + "wunr="
            + self.__user_id,
            "Connection": "Keep-Alive",
            "Referer": f"PHPSESSID={self.__session.session_id};wunr={self.__user_id}",
            "X-Requested-With": "X-Requested-With: XMLHttpRequest",
        }
        adresse = (
            f"http://s{self.__session.server}{STATIC_DOMAIN}{AJAX_PHP}"
            + f"do=statsGetStats&which=0&start=0&additional={self.__user_id}&token={self.__token}"
        )

        response, content = self.__webclient.request(adresse, "GET", headers=headers)
        check_if_http_status_is_ok(response)
        jcontent = parsing_utils.generate_json_content_and_check_for_ok(content)
        return jcontent

    def get_trophies(self):
        """
        Funktion ermittelt, ob die Imkerei verfügbar ist und gibt True/False zurück.
        Dazu muss ein Mindestlevel von 10 erreicht sein und diese dann freigeschaltet sein.
        Die Freischaltung wird anhand eines Geschenks im Spiel geprüft.
        """

        headers = {
            "Cookie": f"PHPSESSID={self.__session.session_id};wunr={self.__user_id}",
            "Connection": "Keep-Alive",
        }
        adresse = (
            f"http://s{self.__session.server}{STATIC_DOMAIN}"
            + f"/ajax/achievements.php?token={self.__token}"
        )

        response, content = self.__webclient.request(adresse, "GET", headers=headers)
        check_if_http_status_is_ok(response)
        return parsing_utils.generate_json_content_and_check_for_ok(content)

    def get_user_profile(self):
        """
        Prüft, ob die E-Mail Adresse im Profil bestätigt ist.
        """
        headers = {
            "User-Agent": USER_AGENT,
            "Cookie": f"PHPSESSID={self.__session.session_id};wunr={self.__user_id}",
        }

        adresse = f"http://s{self.__session.server}{STATIC_DOMAIN}/nutzer/profil.php"

        response, content = self.__webclient.request(adresse, "GET", headers=headers)
        check_if_http_status_is_ok(response)
        return content.decode("utf-8")

    def read_storage_from_server(self):
        headers = {
            "User-Agent": USER_AGENT,
            "Cookie": f"PHPSESSID={self.__session.session_id};wunr={self.__user_id}",
        }

        address = (
            f"http://s{self.__session.server}{STATIC_DOMAIN}/ajax/updatelager.php?all=1"
        )
        response, content = self.__webclient.request(address, "GET", headers=headers)
        check_if_http_status_is_ok(response)
        jcontent = parsing_utils.generate_json_content_and_check_for_ok(content)
        return jcontent["produkte"]

    def update_storage(self):
        headers = {
            "User-Agent": USER_AGENT,
            "Cookie": f"PHPSESSID={self.__session.session_id};wunr={self.__user_id}",
            "Content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "text/javascript, text/html, application/xml, text/xml, */*",
        }

        address = f"http://s{self.__session.server}{STATIC_DOMAIN}/ajax/updatelager.php"
        parameter = urlencode(
            {"all": "1", "sort": "1", "type": "normal", "token": self.__token}
        )
        _, content = self.__webclient.request(
            address, method="POST", body=parameter, headers=headers
        )
        content = parsing_utils.generate_json_content_and_check_for_ok(content)

    def get_all_product_informations(self):
        """
        Sammelt alle Produktinformationen und gibt diese zur Weiterverarbeitung zurück.
        """

        headers = {
            "Cookie": f"PHPSESSID={self.__session.session_id};wunr={self.__user_id}"
        }

        address = f"http://s{self.__session.server}{STATIC_DOMAIN}/main.php?page=garden"
        response, content = self.__webclient.request(address, "GET", headers=headers)
        content = content.decode("UTF-8")
        check_if_http_status_is_ok(response)
        re_token = re.search(r"ajax\.setToken\(\"(.*)\"\);", content)
        self.__token = re_token.group(1)
        return content

    def get_all_tradeable_products(self):
        """
        Gibt eine Liste zurück, welche Produkte handelbar sind.
        """

        headers = {
            "Cookie": f"PHPSESSID={self.__session.session_id};wunr={self.__user_id}",
            "Content-Length": "0",
        }

        adresse = (
            f"http://s{self.__session.server}{STATIC_DOMAIN}{MARKET_API}?show=overview"
        )

        response, content = self.__webclient.request(adresse, "GET", headers=headers)
        check_if_http_status_is_ok(response)
        return content

    def get_npc_prices(self):
        """
        Ermittelt aus der Wurzelimperium-Hilfe die NPC Preise aller Produkte.
        """

        headers = {
            "Cookie": f"PHPSESSID={self.__session.session_id};wunr={self.__user_id}",
            "Content-Length": "0",
        }

        adresse = f"http://s{self.__session.server}{STATIC_DOMAIN}/hilfe.php?item=2"

        response, content = self.__webclient.request(adresse, "GET", headers=headers)
        check_if_http_status_is_ok(response)
        return content.decode("UTF-8")

    def get_notes(self):
        """
        get the users note
        """

        headers = {
            "Cookie": f"PHPSESSID={self.__session.session_id};wunr={self.__user_id}",
            "Content-Length": "0",
        }

        adresse = f"http://s{self.__session.server}{STATIC_DOMAIN}{NOTES_API}"
        response, content = self.__webclient.request(adresse, "GET", headers=headers)
        check_if_http_status_is_ok(response)
        return content.decode("UTF-8")


def check_if_http_status_is_ok(response):
    if not response["status"] == str(HTTPStatus.OK.value):
        raise HTTPStateError("HTTP Status is not ok")
