class LoginData(object):
    def __init__(self, server: int, username: str, password: str):
        if(server<0 or server>46):
            raise ValueError("Server must be Integer, greater than 0 and smaller than 47")
        self.__server = server
        self.__username = username
        self.__password = password

    @property
    def server(self):
        return self.__server

    @property
    def username(self):
        return self.__username

    @property
    def password(self):
        return self.__password
