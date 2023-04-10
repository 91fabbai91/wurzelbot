from typing import Optional
from pydantic import BaseModel, PositiveInt, StrictStr, Field

class Message(BaseModel):
    id: PositiveInt
    recipient: StrictStr
    subject: StrictStr
    body: StrictStr
    delivery_state: Optional[StrictStr] = Field(..., allow_mutation=True)
    sender: Optional[StrictStr] = Field(..., allow_mutation=True)

    
    class Config:
        allow_mutation = False
        validate_assignment = True

    