from . import http_connection
import logging
import time

class Garden(object):
    def __init__(self, http_connection: http_connection.HTTPConnection, garden_id: int):
        self.__id = garden_id
        self.__len_x = 17
        self.__len_y = 12
        self.__logger = logging.getLogger("Garden_" + self.__id)
        self.__logger.setLevel(logging.DEBUG)
        self.__http_connection = http_connection
        self.__number_of_fields = self.__len_x * self.__len_y

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

    def _get_all_field_ids_from_field_id_and_size_as_string(self, field_id, sx, sy):
        """
        Rechnet anhand der field_id und Größe der Pflanze (sx, sy) alle IDs aus und gibt diese als String zurück.
        """
        
        # Zurückgegebene Felderindizes (x) für Pflanzen der Größe 1-, 2- und 4-Felder.
        # Wichtig beim Gießen; dort müssen alle Indizes angegeben werden.
        # (Sowohl die mit x als auch die mit o gekennzeichneten).
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

    def _get_all_field_ids_from_field_id_and_size_as_int_list(self, field_id, sx, sy):
        """
        Rechnet anhand der field_id und Größe der Pflanze (sx, sy) alle IDs aus und gibt diese als Integer-Liste zurück.
        """
        sFields =self._get_all_field_ids_from_field_id_and_size_as_string(field_id, sx, sy)
        listFields = sFields.split(',') #Stringarray
                        
        for i in range(0, len(listFields)):
            listFields[i] = int(listFields[i])
            
        return listFields
    
    def __is_plant_growable_on_field(self, field_id, empty_fields, fields_to_plant, sx):
        """
        Prüft anhand mehrerer Kriterien, ob ein Anpflanzen möglich ist.
        """
        # Betrachtetes Feld darf nicht besetzt sein
        if not (field_id in empty_fields): return False
        
        # Anpflanzen darf nicht außerhalb des Gartens erfolgen
        # Dabei reicht die Betrachtung in x-Richtung, da hier ein
        # "Zeilenumbruch" stattfindet. Die y-Richtung ist durch die
        # Abfrage abgedeckt, ob alle benötigten Felder frei sind.
        # Felder außerhalb (in y-Richtung) des Gartens sind nicht leer,
        # da sie nicht existieren.
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

    def get_weed_fields(self):
        jcontent = self.__http_connection.execute_command('do=changeGarden&garden=' + \
                  str(self.__id))
        return self.__find_weed_fields_from_json_content(jcontent)

    def __find_empty_fields_from_json_content(self, jcontent):
        """
        Sucht im JSON Content nach Felder die leer sind und gibt diese zurück.
        """
        empty_fields = []
        
        for field in jcontent['garden']:
            if jcontent['garden'][field][0] == 0:
                empty_fields.append(int(field))

        #Sortierung über ein leeres Array ändert Objekttyp zu None
        if len(empty_fields) > 0:
            empty_fields.sort(reverse=False)

        return empty_fields

    def __find_weed_fields_from_json_content(self, jcontent):
        """
        Sucht im JSON Content nach Felder die mit Unkraut befallen sind und gibt diese zurück.
        """
        weed_fields = []
        
        # 41 Unkraut, 42 Baumstumpf, 43 Stein, 45 Maulwurf
        for field in jcontent['garden']:
            if jcontent['garden'][field][0] in [41, 42, 43, 45]:
                weed_fields.append(int(field))

        #Sortierung über ein leeres Array ändert Objekttyp zu None
        if len(weed_fields) > 0:
            weed_fields.sort(reverse=False)

        return weed_fields

    def harvest(self):
        self.__http_connection.execute_command('do=changeGarden&garden=' + self.__id)
        self.__http_connection.execute_command('do=gardenHarvestAll')

    def grow_plants(self, plant_id, sx, sy, amount):
        planted = 0
        empty_fields = self.get_empty_fields()
        
        try:
            for field in range(1, self.__number_of_fields + 1):
                if planted == amount: break
            
                fields_to_plant =self._get_all_field_ids_from_field_id_and_size_as_string(field, sx, sy)
                
                if (self.__is_plant_growable_on_field(field, empty_fields, fields_to_plant, sx)):
                        fields =self._get_all_field_ids_from_field_id_and_size_as_string(field, sx, sy)
                        self.__http_connection.grow_plants(field, plant_id, self.__id, fields)
                        planted += 1

                        #Nach dem Anbau belegte Felder aus der Liste der leeren Felder loeschen
                        fields_to_plantSet = set(fields_to_plant)
                        empty_fieldsSet = set(empty_fields)
                        tmpSet = empty_fieldsSet - fields_to_plantSet
                        empty_fields = list(tmpSet)

        except:
            self.__logger.error('Im Garten ' + str(self.__id) + ' konnte nicht gepflanzt werden.')
            return 0    
        else:
            msg = 'Im Garten ' + str(self.__id) + ' wurden ' + str(planted) + ' Pflanzen gepflanzt.'
            self.__logger.info(msg)
            print(msg)
            return planted

    def __find_plants_to_be_watered_from_json_content(self, jContent):
        """
        Sucht im JSON Content nach Pflanzen die bewässert werden können und gibt diese inkl. der Pflanzengröße zurück.
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
        self.__logger.info('Gieße alle Pflanzen im Garten ' + str(self.__id) + '.')
        try:
            jcontent = self.__http_connection.execute_command('do=changeGarden&garden=' + \
                  str(self.__id))
            plants = self.__find_plants_to_be_watered_from_json_content(jcontent)
            nPlants = len(plants['fieldID'])
            for i in range(0, nPlants):
                sFields =self._get_all_field_ids_from_field_id_and_size_as_string(plants['fieldID'][i], plants['sx'][i], plants['sy'][i])
                self.__http_connection.waterPlantInGarden(self.__id, plants['fieldID'][i], sFields)
        except:
            self.__logger.error('Garten ' + str(self.__id) + ' konnte nicht bewässert werden.')
        else:
            self.__logger.info('Im Garten ' + str(self.__id) + ' wurden ' + str(nPlants) + ' Pflanzen gegossen.')
            print('Im Garten ' + str(self.__id) + ' wurden ' + str(nPlants) + ' Pflanzen gegossen.')

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
                sFields = self._get_all_field_ids_from_field_id_and_size_as_string(plants['fieldID'][i], plants['sx'][i], plants['sy'][i])
                self.__http_connection.waterPlantInAquaGarden(plants['fieldID'][i], sFields)
        except:
            self.__logger.error('Wassergarten konnte nicht bewässert werden.')
        else:
            self.__logger.info('Im Wassergarten wurden ' + str(nPlants) + ' Pflanzen gegossen.')

    def harvest(self):
        self.__http_connection.execute_command('do=watergardenHarvestAll')