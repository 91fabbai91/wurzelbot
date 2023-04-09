import re
import io
import logging
import xml.etree.ElementTree as eTree
import json
import http_connection
import product


class ProductInformation(object):

    def __init__(self, http_connection: http_connection.HTTPConnection) -> None:
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__http_connection = http_connection
        self.__products = []
        self.init_all_products()

    def __set_all_prices_of_npc(self):
        """
        Ermittelt alle möglichen NPC Preise und setzt diese in den Produkten.
        """
        
        content = self.__http_connection.get_npc_prices()
        content = content.decode('UTF-8').replace('Gärten & Regale', 'Gärten und Regale')
        content = bytearray(content, encoding='UTF-8')

        dictNPCPrices = self.__parse_npc_prices_from_html(content)
        #except:
        #    pass #TODO Exception definieren
        #else:
        dNPCKeys = dictNPCPrices.keys()
        
        for product in self.__products:
            productname = product.name
            if productname in dNPCKeys:
                product.price_npc = dictNPCPrices[productname]

    def init_all_products(self):
        """
        Initialisiert alle Produkte.
        """
        content = self.__http_connection.get_all_product_informations()
        reProducts = re.search(r'data_products = ({.*}});var', content)
        products = reProducts.group(1)
        jProducts = json.loads(products)
        dictProducts = dict(jProducts)
        keys = dictProducts.keys()
        keys = sorted(keys)
        # Nicht genutzte Attribute: img, imgPhase, fileext, clear, edge, pieces, speedup_cooldown in Kategorie z
        for key in keys:
                # 999 ist nur ein Testeintrag und wird nicht benötigt.
            if key == '999':
                continue

            name = dictProducts[key]['name'].replace('&nbsp;', ' ')
            self.__products.append(product.Product(id= int(key), \
                                            cat       = dictProducts[key]['category'], \
                                            sx        = dictProducts[key]['sx'], \
                                            sy        = dictProducts[key]['sy'], \
                                            name      = name, \
                                            lvl       = dictProducts[key]['level'], \
                                            crop      = dictProducts[key]['crop'], \
                                            plantable = dictProducts[key]['plantable'], \
                                               time      = dictProducts[key]['time']))
                
        self.__set_all_prices_of_npc()

    def get_product_by_id(self, id) -> product.Product:
        for product in self.__products:
            if int(id) == int(product.id): return product
            
    def get_product_by_name(self, name : str) -> product.Product:
        for product in self.__products:
            if (name.lower() == product.name.lower()): return product
        for product in self.__products:
            if (name.lower() in product.name.lower()): return product
        return None

    def get_list_of_all_product_ids(self) -> list:
        
        product_id_list = []
        
        for product in self.__products:
            id = product.id
            product_id_list.append(id)
            
        return product_id_list

    def __parse_npc_prices_from_html(self, html: bytearray):
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