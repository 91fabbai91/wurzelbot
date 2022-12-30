import json
from sre_constants import SUCCESS
import yaml
import logging




def generate_json_content_and_check_for_ok(content : str):
    """
    Preparation and verification of JSON data received from the server.
    """
    jContent = json.loads(content)
    if (jContent['status'] == 'ok'): return jContent
    else: logging.error(f"JSON not ok. {jContent['message']}")

def generate_json_content_and_check_for_success(content):
    """
    Parsing all NPC prices from the HTML script of the game help.
    """
    jContent = json.loads(content)
    try:
        if (jContent['success'] == 1): return jContent
    except:
        pass
    else: logging.error(f"JSON not successful. {jContent['errorMsg']}")

def generate_json_content_and_check_for_status_success(content):
    """
    Parsing all NPC prices from the HTML script of the game help.
    """
    jContent = json.loads(content)
    try:
        if (jContent['status'] == 'SUCCESS'): return jContent
    except:
        pass
    else: logging.error('JSON not successful')




def generate_yaml_content_and_check_status_for_ok(content: str):
    """
    Preparation and checking of YAML data received from the server for iO status.
    """
    content = content.replace('\n', ' ')
    content = content.replace('\t', ' ')
    yContent = yaml.load(content, Loader=yaml.FullLoader)
    
    if (yContent['status'] != 'ok'):
        raise YAMLError("YAMLError")

def generate_yaml_content_and_check_for_success(content : str):
    """
    Aufbereitung und Prüfung der vom Server empfangenen YAML Daten auf Erfolg.
    """
    content = content.replace('\n', ' ')
    content = content.replace('\t', ' ')
    yContent = yaml.load(content, Loader=yaml.FullLoader)
    
    if (yContent['success'] != 1):
        raise YAMLError("YAML Error")



class JSONError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class HTTPStateError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class YAMLError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)