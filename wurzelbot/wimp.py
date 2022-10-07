class Wimp(object):
    def __init__(self, id: int, product_amount: list, reward: float) -> None:
        self.__product_amount = product_amount
        self.__id = id
        self.__reward = reward
    
    @property
    def product_amount(self):
        return self.__product_amount

    @property
    def id(self):
        return self.__id
    
    @property
    def reward(self):
        return self.__reward
    

