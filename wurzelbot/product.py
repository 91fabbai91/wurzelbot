import logging
from typing import Optional
from pydantic import BaseModel, Field, PositiveFloat, StrictStr, StrictBool, StrictInt

class Product(BaseModel):
    id: StrictInt = Field(default=None, allow_mutation=False, strict=True)
    cat: StrictStr  = Field(...,allow_mutation=False)
    sx: Optional[StrictInt] = Field(...,allow_mutation=False)
    sy: Optional[StrictInt]  = Field(...,allow_mutation=False)
    name: StrictStr  = Field(...,allow_mutation=False)
    lvl: StrictInt  = Field(...,allow_mutation=False)
    crop: StrictInt  = Field(...,allow_mutation=False)
    is_plantable: Optional[StrictBool]  = Field(...,allow_mutation=False)
    time: StrictInt = Field(...,allow_mutation=False)
    price_npc: Optional[PositiveFloat]

    class Config:
        validate_assignment = True
    

   
    def is_plant(self):
        return self.cat == "v"
    
    def is_decoration(self):
        return self.cat == "d"

