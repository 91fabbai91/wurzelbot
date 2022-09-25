import time, logging


class Session(object):
    """
    Die Session Klasse ist das Python-Pendant einer PHP-Session und dieser daher nachempfunden.
    """

    #Gültigkeitsdauer der Session (2 h -> 7200 s)
    __lifetime         = 7200
    __lifetime_reserve =  300

    #Eine Reservezeit dient dazu, kurz vor Ende der Session rechtzeitig alle Aktionen
    #abschließen zu können
    
    def __init__(self):
        """
        Initialisierung aller Attribute mit einem Standardwert.
        """
        self.__logger = logging.getLogger(self.__class__.__name__+ "_" + self.__session_id)
        self.__session_id = None
        self.__server = None
        self.__start_time = None
        self.__end_time = None
 

    def is_session_time_elapsed(self):
        """
        Prüft, ob die offene Session abgelaufen ist.
        """
        current_time = time.time()
        if (current_time > self.__end_time):
            return True
        else:
            return False


    def is_session_valid(self): #TODO: Prüfen wie die Methode sinnvoll eingesetzt werden kann
        """
        Prüft anhand verschiedener Kriterien, ob die aktuelle Session gültig ist.
        """
        bReturn = True
        if (self.__session_id == None): bReturn = False
        if (self.is_session_time_elapsed()): bReturn = False
        return bReturn


    def open_session(self, sessionID, server):
        """
        Anlegen einer neuen Session mit allen notwendigen Daten.
        """
        self.__session_id = sessionID
        self.__server = server
        
        self.__start_time = time.time()
        self.__end_time = self.__start_time + (self.__lifetime - self.__lifetime_reserve)
        
        sID = str(self.__session_id)
        self.__logger.info("Session (ID: " + sID + ") geöffnet")


    def closeSession(self, wunr, server):
        """
        Zurücksetzen aller Informationen. Gleichbedeutend mit einem Schließen der Session.
        """
        sID = str(self.__session_id)
        self.__session_id = None
        self.__server = None
        self.__start_time = None
        self.__end_time = None
        self.__logger.info("Session (ID: " + sID + ") geschlossen")

    
    def get_remaining_time(self):
        """
        Gibt die verbleibende Zeit zurück, bis die Session abläuft.
        """
        current_time = time.time()
        return self.__end_time - current_time


    @property
    def session_id(self):
        """
        Gibt die Session-ID zurück.
        """
        return self.__session_id


    @property
    def server(self):
        """
        Gibt die Servernummer zurück.
        """
        return self.__server


        