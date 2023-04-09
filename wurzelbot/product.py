import logging
from typing import Optional
from pydantic import BaseModel

class Product(BaseModel):
    id: int
    cat: str
    sx: Optional[int] 
    sy: Optional[int]
    name: str
    lvl: int
    crop: int
    is_plantable: Optional[bool]
    time: int
    price_npc: Optional[float]
    

   
    def is_plant(self):
        return self.category == "v"
    
    def is_decoration(self):
        return self.category == "d"

