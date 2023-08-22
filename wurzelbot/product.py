from typing import Optional
from pydantic import ConfigDict, BaseModel, Field, PositiveFloat, StrictStr, StrictBool, StrictInt

class Product(BaseModel):
    id: StrictInt = Field(default=None, frozen=True, strict=True)
    cat: StrictStr  = Field(...,frozen=True)
    sx: Optional[StrictInt] = Field(None,frozen=True)
    sy: Optional[StrictInt]  = Field(None,frozen=True)
    name: StrictStr  = Field(...,frozen=True)
    lvl: StrictInt  = Field(...,frozen=True)
    crop: StrictInt  = Field(...,frozen=True)
    is_plantable: Optional[StrictBool]  = Field(None,frozen=True)
    time: StrictInt = Field(...,frozen=True)
    price_npc: Optional[PositiveFloat] = None
    model_config = ConfigDict(validate_assignment=True)
    

   
    def is_plant(self):
        return self.cat == "v"
    
    def is_decoration(self):
        return self.cat == "d"

