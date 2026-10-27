from typing import Optional, Union

from pydantic import BaseModel, ConfigDict, Field, PositiveInt, StrictInt, StrictStr


class Message(BaseModel):
    id: PositiveInt = Field(..., frozen=True)
    recipient: StrictStr = Field(..., frozen=True)
    subject: StrictStr = Field(..., frozen=True)
    body: StrictStr = Field(..., frozen=True)
    delivery_state: Optional[Union[StrictInt, StrictStr]] = Field(None, frozen=False)
    sender: Optional[StrictStr] = Field(None, frozen=False)
    model_config = ConfigDict(frozen=False, validate_assignment=True)

    @property
    def state(self):
        return self.delivery_state
