import io
import json
from sre_constants import SUCCESS
import yaml
import xml.etree.ElementTree as eTree

def generate_json_content_and_check_for_ok(content : str):
    """
    Preparation and verification of JSON data received from the server.
    """
    jContent = json.loads(content)
    if (jContent['status'] == 'ok'): return jContent
    else: raise JSONError('JSON not ok')

def generate_json_content_and_check_for_success(content):
    """
    Parsing all NPC prices from the HTML script of the game help.
    """
    jContent = json.loads(content)
    try:
        if (jContent['success'] == 1): return jContent
    except:
        pass
    else: raise JSONError('JSON not successful')

def generate_json_content_and_check_for_status_success(content):
    """
    Parsing all NPC prices from the HTML script of the game help.
    """
    jContent = json.loads(content)
    try:
        if (jContent['status'] == 'SUCCESS'): return jContent
    except:
        pass
    else: raise JSONError('JSON not successful')


def parse_npc_prices_from_html(html: str):
    """
    Parsing all NPC prices from the HTML script of the game help.
    """
    # ElementTree needs a file to parse.
    # With BytesIO a file is created in memory, not on disk.
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

def get_username_from_json_content(jContent):
    """
    Searches for the username in the passed JSON object and returns it.
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
        raise JSONError('username not found')

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