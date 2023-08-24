import json
import logging

import yaml


def generate_json_content_and_check_for_ok(content: str):
    """
    Preparation and verification of JSON data received from the server.
    """
    jcontent = json.loads(content)
    if jcontent["status"] == "ok":
        return jcontent
    else:
        logging.error(f"JSON not ok. {jcontent['message']}")


def generate_json_content_and_check_for_success(content):
    """
    Parsing all NPC prices from the HTML script of the game help.
    """
    jcontent = json.loads(content)
    try:
        if jcontent["success"] == 1:
            return jcontent
    except:
        logging.error(f"JSON not successful. {jcontent['errorMsg']}")


def generate_json_content_and_check_for_status_success(content):
    """
    Parsing all NPC prices from the HTML script of the game help.
    """
    jcontent = json.loads(content)

    if jcontent["status"] == "SUCCESS":
        return jcontent
    logging.error("JSON not successful")


def generate_yaml_content_and_check_status_for_ok(content: str):
    """
    Preparation and checking of YAML data received from the server for iO status.
    """
    content = content.replace("\n", " ")
    content = content.replace("\t", " ")
    ycontent = yaml.load(content, Loader=yaml.FullLoader)

    if ycontent["status"] != "ok":
        raise YAMLError("YAMLError")


def generate_yaml_content_and_check_for_success(content: str):
    """
    Aufbereitung und Prüfung der vom Server empfangenen YAML Daten auf Erfolg.
    """
    content = content.replace("\n", " ")
    content = content.replace("\t", " ")
    ycontent = yaml.load(content, Loader=yaml.FullLoader)

    if ycontent["success"] != 1:
        raise YAMLError("YAML Error")


class JSONError(Exception):
    def __init__(self, value):
        super().__init__(value)
        self.value = value

    def __str__(self):
        return repr(self.value)


class HTTPStateError(Exception):
    def __init__(self, value):
        super().__init__(value)
        self.value = value

    def __str__(self):
        return repr(self.value)


class YAMLError(Exception):
    def __init__(self, value):
        super().__init__(value)
        self.value = value

    def __str__(self):
        return repr(self.value)
