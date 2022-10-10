import logging
import time
import http_connection
import parsing_utils
from datetime import datetime
from enum import Enum
from collections import Counter


class Garden(object):
    def __init__(self, http_connection1: http_connection.HTTPConnection, garden_id: int):
        self.__id = garden_id
        self.__len_x = 17
        self.__len_y = 12
        self.__logger = logging.getLogger("Garden{id}".format(id=self.__id))
        self.__logger.setLevel(logging.DEBUG)
        self.__http_connection = http_connection1
        self.__number_of_fields = self.__len_x * self.__len_y
        self.__fields = []
        self.update_planted_fields()

    @property
    def id(self):
        return self.__id


    @property
    def len_x(self):
        return self.__len_x

    @property
    def len_y(self):
        return self.__len_y

    @property
    def number_of_fields(self):
        return self.__number_of_fields

    @property
    def fields(self):
        return self.__fields

    def number_planted_plants(self, plant_id: int):
        number_plants = 0
        for field in self.__fields:
            if int(field[1]) == plant_id:
                number_plants=number_plants+1
        return number_plants

        

    def __get_all_field_ids_from_field_id_and_size_as_string(self, field_id, sx, sy):
        """
        Calculates all IDs based on the field_id and size of the plant (sx, sy) and returns them as a string.
        """
        
        # Returned field indices (x) for plants of size 1, 2 and 4 fields.
        # Important when watering; all indices must be specified there.
        # (Both those marked with x and those marked with o).
        # x: field_id
        # o: ergänzte Felder anhand der size
        # +---+   +---+---+   +---+---+
        # | x |   | x | o |   | x | o |
        # +---+   +---+---+   +---+---+
        #                     | o | o |
        #                     +---+---+
        
        if (sx == 1 and sy == 1): return str(field_id)
        if (sx == 2 and sy == 1): return str(field_id) + ',' + str(field_id + 1)
        if (sx == 1 and sy == 2): return str(field_id) + ',' + str(field_id + 17)
        if (sx == 2 and sy == 2): return str(field_id) + ',' + str(field_id + 1) + ',' + str(field_id + 17) + ',' + str(field_id + 18)
        self.__logger.debug('Error der plant_size --> sx: ' + str(sx) + ' sy: ' + str(sy))

    def __get_all_field_ids_from_field_id_and_size_as_int_list(self, field_id, sx, sy):
        """
        Calculates all IDs based on the field_id and size of the plant (sx, sy) and returns them as an integer list.
        """
        sFields =self.__get_all_field_ids_from_field_id_and_size_as_string(field_id, sx, sy)
        listFields = sFields.split(',') #Stringarray
                        
        for i in range(0, len(listFields)):
            listFields[i] = int(listFields[i])
            
        return listFields
    
    def __is_plant_growable_on_field(self, field_id, empty_fields, fields_to_plant, sx):
        """
        Checks against several criteria to see if planting is possible.
        """
        # Betrachtetes Feld darf nicht besetzt sein
        if not (field_id in empty_fields): return False
        
        # Planting must not be done outside the garden
        # The consideration in x-direction is sufficient, because here a
        # "line break" takes place. The y-direction is covered by the
        # query whether all required fields are empty.
        # Fields outside (in y-direction) of the garden are not empty,
        # since they do not exist.

        if not ((self.__number_of_fields - field_id)%self.__len_x >= sx - 1): return False
        fields_to_plantSet = set(fields_to_plant)
        empty_fieldsSet = set(empty_fields)
        
        # Alle benötigten Felder der Pflanze müssen leer sein
        if not (fields_to_plantSet.issubset(empty_fieldsSet)): return False
        return True
    

    def get_empty_fields(self):
        jcontent = self.__http_connection.execute_command('do=changeGarden&garden=' + \
                  str(self.__id))
        return self.__find_empty_fields_from_json_content(jcontent)

    def get_blocked_fields(self):
        jcontent = self.__http_connection.execute_command('do=changeGarden&garden=' + \
                  str(self.__id))
        return self.__find_blocked_fields_from_json_content(jcontent)

    def destroy_weed_fields(self):
        number_freed_fields = 0
        blocked_fields = self.get_blocked_fields()
        blocked_fields_type_count = Counter(list(blocked_fields.values()))
        try:
            if(blocked_fields_type_count[BlockedFieldType.WEED.value] >0): 
                blocked_field_type = BlockedFieldType.WEED
                number_freed_fields = number_freed_fields + self.__destroy_fields_of_type(blocked_fields, blocked_field_type)
            elif(blocked_fields_type_count[BlockedFieldType.STONE.value] >0):
                blocked_field_type = BlockedFieldType.STONE
                number_freed_fields = number_freed_fields + self.__destroy_fields_of_type(blocked_fields, blocked_field_type)
            elif(blocked_fields_type_count[BlockedFieldType.TREE_STUMP.value] >0):
                blocked_field_type = BlockedFieldType.TREE_STUMP
                number_freed_fields = number_freed_fields + self.__destroy_fields_of_type(blocked_fields, blocked_field_type)
            elif(blocked_fields_type_count[BlockedFieldType.MOLE.value] > 0):
                blocked_field_type = BlockedFieldType.MOLE
                number_freed_fields = number_freed_fields + self.__destroy_fields_of_type(blocked_fields, blocked_field_type)
            else:
                self.__logger.info("No blocked fields available!")
                return 0
        except parsing_utils.JSONError as exception:
            self.__logger.error(exception)
        else:
            self.__logger.info("Number of freed fields: {fields}".format(fields=number_freed_fields))
            return number_freed_fields

    def __destroy_fields_of_type(self, blocked_fields, blocked_field_type) -> int:
        number_freed_fields = 0
        for field_id, field_type in blocked_fields.items():  
            if field_type == blocked_field_type.value:
                parsing_utils.generate_json_content_and_check_for_success(self.__http_connection.destroy_weed_field(field_id))
                self.__logger.debug("Field Nr. {field_id} of type {field_type} freed".format(field_id= field_id, field_type=field_type))
                number_freed_fields = number_freed_fields + 1
        return number_freed_fields

    def update_planted_fields(self):
        jcontent = self.__http_connection.execute_command('do=changeGarden&garden=' + \
                  str(self.__id))
        plants =  self.__get_plants_on_fields(jcontent)
        return plants

    def __get_plants_on_fields(self, jcontent):
        self.__fields = []
        for field in jcontent['grow']:
            field[3] = datetime.fromtimestamp(int(field[3]))
            self.__fields.append(field)
        return self.__fields


    def __find_empty_fields_from_json_content(self, jcontent):
        """
        Searches the JSON content for fields that are empty and returns them.
        """
        empty_fields = []
        
        for field in jcontent['garden']:
            if jcontent['garden'][field][0] == 0:
                empty_fields.append(int(field))

        #Sorting over an empty array changes object type to None
        if len(empty_fields) > 0:
            empty_fields.sort(reverse=False)

        return empty_fields

    def __find_blocked_fields_from_json_content(self, jcontent):
        """
        Searches the JSON content for fields that are infested with weeds and returns them.
        """
        weed_fields = {}
        
        # 41 weed, 42 tree stump, 43 stone, 45 mole
        for field in jcontent['garden']:
            blocked_field_type = jcontent['garden'][field][0]
            if blocked_field_type in [BlockedFieldType.WEED.value, BlockedFieldType.STONE.value, BlockedFieldType.TREE_STUMP.value, BlockedFieldType.MOLE.value]:
                weed_fields.update({int(field): blocked_field_type})


        return weed_fields

    def harvest(self):
        self.__http_connection.execute_command('do=changeGarden&garden={id}'.format(id=self.__id))
        self.__http_connection.execute_command('do=gardenHarvestAll')

    def grow_plants(self, plant_id, sx, sy, amount):
        planted = 0
        empty_fields = self.get_empty_fields()
        
        try:
            for field in range(1, self.__number_of_fields + 1):
                if planted == amount: break
            
                fields_to_plant =self.__get_all_field_ids_from_field_id_and_size_as_int_list(field, sx, sy)
                
                if (self.__is_plant_growable_on_field(field, empty_fields, fields_to_plant, sx)):
                        fields =self.__get_all_field_ids_from_field_id_and_size_as_string(field, sx, sy)
                        self.__http_connection.grow_plant(field, plant_id, self.__id, fields)
                        planted += 1

                        #Delete occupied fields from the list of empty fields after cultivation
                        fields_to_plantSet = set(fields_to_plant)
                        empty_fieldsSet = set(empty_fields)
                        tmpSet = empty_fieldsSet - fields_to_plantSet
                        empty_fields = list(tmpSet)

        except Exception as e:
            self.__logger.error(e)
            self.__logger.error('In garden ' + str(self.__id) + ' could not get planted.')
            return 0    
        else:
            msg = 'In garden ' + str(self.__id) + ' were ' + str(planted) + ' plants planted.'
            self.__logger.info(msg)
            return planted

    def __find_plants_to_be_watered_from_json_content(self, jContent):
        """
        Searches the JSON content for plants that can be watered and returns them including the plant size.
        """
        plants_to_be_watered = {'fieldID':[], 'sx':[], 'sy':[]}
        for field in range(0, len(jContent['grow'])):
            planted_field_id = jContent['grow'][field][0]
            plant_size = jContent['garden'][str(planted_field_id)][9]
            splittedPlantSize = str(plant_size).split('x')
            sx = splittedPlantSize[0]
            sy = splittedPlantSize[1]
            
            if not self.__is_field_watered(jContent, planted_field_id):
                field_id_to_be_watered = planted_field_id
                plants_to_be_watered['fieldID'].append(field_id_to_be_watered)
                plants_to_be_watered['sx'].append(int(sx))
                plants_to_be_watered['sy'].append(int(sy))

        return plants_to_be_watered


    def __is_field_watered(self, jContent, fieldID):
        """
        Ermittelt, ob ein Feld fieldID gegossen ist und gibt True/False zurück.
        Ist das Datum der Bewässerung 0, wurde das Feld noch nie gegossen.
        Eine Bewässerung hält 24 Stunden an. Liegt die Zeit der letzten Bewässerung
        also 24 Stunden + 30 Sekunden (Sicherheit) zurück, wurde das Feld zwar bereits gegossen,
        kann jedoch wieder gegossen werden.
        """
        one_day_in_seconds = (24*60*60) + 30
        current_time_in_seconds = time.time()
        water_date_in_seconds = int(jContent['water'][fieldID-1][1])

        if water_date_in_seconds == '0': return False
        elif (current_time_in_seconds - water_date_in_seconds) > one_day_in_seconds: return False
        else: return True

    def water_plants(self):
        self.__logger.info('Water all plants in garden ' + str(self.__id) + '.')
        try:
            jcontent = self.__http_connection.execute_command('do=changeGarden&garden=' + \
                  str(self.__id))
            plants = self.__find_plants_to_be_watered_from_json_content(jcontent)
            nPlants = len(plants['fieldID'])
            for i in range(0, nPlants):
                sFields =self.__get_all_field_ids_from_field_id_and_size_as_string(plants['fieldID'][i], plants['sx'][i], plants['sy'][i])
                self.__http_connection.water_plant(self.__id, plants['fieldID'][i], sFields)
        except Exception as e:
            self.__logger.error(e)
            self.__logger.error('Garden ' + str(self.__id) + ' could not get watered.')
        else:
            self.__logger.info('In garden ' + str(self.__id) + ' were ' + str(nPlants) + ' plants watered.')

    def get_wimps_data(self):
        self.__http_connection.execute_command("do=changeGarden&garden={id}".format(id=self.__id))
        jcontent = self.__http_connection.execute_wimp_command("do=getAreaData")
        return parsing_utils.get_wimps_list_from_json_content(jcontent)



class AquaGarden(Garden):
    def __init__(self, http_connection):
        super(http_connection, 101)


    def water_plants(self):
        """
        Alle Pflanzen im Wassergarten werden bewässert.
        """
        try:
            jcontent = self.__http_connection.getPlantsToWaterInAquaGarden()
            plants = self.__find_plants_to_be_watered_from_json_content(jcontent)
            nPlants = len(plants['fieldID'])
            for i in range(0, nPlants):
                sFields = self.__get_all_field_ids_from_field_id_and_size_as_string(plants['fieldID'][i], plants['sx'][i], plants['sy'][i])
                self.__http_connection.waterPlantInAquaGarden(plants['fieldID'][i], sFields)
        except:
            self.__logger.error('Watergarden could not get watered.')
        else:
            self.__logger.info('In water garden were ' + str(nPlants) + ' plants watered.')

    def harvest(self):
        self.__http_connection.execute_command('do=watergardenHarvestAll')

class BlockedFieldType(Enum):
    WEED = 41
    TREE_STUMP = 42
    STONE = 43
    MOLE = 45