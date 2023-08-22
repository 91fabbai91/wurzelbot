from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, PositiveInt, StrictStr


class Message(BaseModel):
    id: PositiveInt
    recipient: StrictStr
    subject: StrictStr
    body: StrictStr
    delivery_state: Optional[StrictStr] = Field(None, frozen=False)
    sender: Optional[StrictStr] = Field(None, frozen=False)
    model_config = ConfigDict(frozen=True, validate_assignment=True)
