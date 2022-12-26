import time, logging


class Session(object):
    """
    The session class is the Python counterpart of a PHP session and is therefore modeled after it.
    """

    #Session validity period (2 h -> 7200 s)
    __lifetime         = 7200
    __lifetime_reserve =  300

    # A reserve time is used to be able to complete all actions in time shortly before the end of the session.
    # to be able to complete
    
    def __init__(self):
        """
        Initialization of all attributes with a default value.
        """
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__session_id = None
        self.__server = None
        self.__start_time = None
        self.__end_time = None
 

    def is_session_time_elapsed(self):
        """
        Checks if the open session has expired.
        """
        current_time = time.time()
        if (current_time > self.__end_time):
            return True
        else:
            return False


    def is_session_valid(self): 
        """
        Checks whether the current session is valid based on various criteria.
        """
        bReturn = True
        if (self.__session_id == None): bReturn = False
        if (self.is_session_time_elapsed()): bReturn = False
        return bReturn


    def open_session(self, sessionID, server):
        """
        Create a new session with all necessary data.
        """
        self.__session_id = sessionID
        self.__server = server
        
        self.__start_time = time.time()
        self.__end_time = self.__start_time + (self.__lifetime - self.__lifetime_reserve)
        
        sID = str(self.__session_id)
        self.__logger.info(f"Session (ID: {sID}) opened")


    def closeSession(self, wunr, server):
        """
        Resetting all information. Equivalent to closing the session.
        """
        sID = str(self.__session_id)
        self.__session_id = None
        self.__server = None
        self.__start_time = None
        self.__end_time = None
        self.__logger.info(f"Session (ID: {sID}) closed")

    
    def get_remaining_time(self):
        """
        Returns the remaining time until the session expires.
        """
        current_time = time.time()
        return self.__end_time - current_time


    @property
    def session_id(self):
        """
        Returns the session ID.
        """
        return self.__session_id


    @property
    def server(self):
        """
        Returns the server number.
        """
        return self.__server


        