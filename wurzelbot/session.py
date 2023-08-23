import logging
import time


class Session:
    """
    The session class is the Python counterpart of a PHP session and is therefore modeled after it.
    """

    # Session validity period (2 h -> 7200 s)
    __lifetime = 7200
    __lifetime_reserve = 300

    # A reserve time is used to be able to complete all actions in time shortly
    # before the end of the session.
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
        return bool(current_time > self.__end_time)

    def is_session_valid(self):
        """
        Checks whether the current session is valid based on various criteria.
        """
        b_return = True
        if self.__session_id is None:
            b_return = False
        if self.is_session_time_elapsed():
            b_return = False
        return b_return

    def open_session(self, session_id, server):
        """
        Create a new session with all necessary data.
        """
        self.__session_id = session_id
        self.__server = server

        self.__start_time = time.time()
        self.__end_time = self.__start_time + (
            self.__lifetime - self.__lifetime_reserve
        )

        s_id = str(self.__session_id)
        self.__logger.info(f"Session (ID: {s_id}) opened")

    def close_session(self):
        """
        Resetting all information. Equivalent to closing the session.
        """
        s_id = str(self.__session_id)
        self.__session_id = None
        self.__server = None
        self.__start_time = None
        self.__end_time = None
        self.__logger.info(f"Session (ID: {s_id}) closed")

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
