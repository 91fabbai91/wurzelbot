from pydantic import BaseModel

class Wimp(BaseModel):
    id: int
    product_amount: dict
    reward: float



    

