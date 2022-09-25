class Product():
    
    def __init__(self, id, cat, sx, sy, name, lvl, crop, plantable, time):
        self.__id = id
        self.__category = cat
        self.__sx = sx
        self.__sy = sy
        self.__name = name.decode('UTF-8')
        self.__level = lvl
        self.__crop = crop
        self.__is_plantable = plantable
        self.__timeUntilHarvest = time
        self.__price_npc = None
   
    @property
    def id(self):
        return self.__id

    @property
    def category(self):
        return self.__category

    @property
    def name(self):
        return self.__name
    
    @property
    def sx(self):
        return self.__sx

    @property
    def sy(self):
        return self.__sy
    
    @property
    def price_npc(self):
        return self.__price_npc
    
    @property
    def is_plantable(self):
        return self.__is_plantable

   
    def is_plant(self):
        return self.__category == "v"
    
    def is_decoration(self):
        return self.__category == "d"

    @price_npc.setter
    def price_npc(self, price):
        self.__price_npc = price
        
    def print_all(self):
        # Show nothing instead of None
        xstr = lambda s: s or ""

        print('ID:', str(self.__id).rjust(3), ' ', \
              'CAT:', str(self.__category).ljust(5), ' ', \
              'Name:', str(self.__name).ljust(35), ' ', \
              'Plantable:', str(self.__is_plantable).ljust(5), ' ', \
              'NPC:', str(xstr(self.__price_npc)).rjust(6), ' ', \
              'SX:', str(xstr(self.__sx)), ' ', \
              'SY:', str(xstr(self.__sy)))

