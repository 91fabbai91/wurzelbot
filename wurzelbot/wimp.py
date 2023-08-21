from pydantic import BaseModel, PositiveInt, PositiveFloat

class Wimp(BaseModel):
    id: PositiveInt
    product_amount: dict
    reward: PositiveFloat



    class Config:
        frozen = True
        validate_assignment = True



    

