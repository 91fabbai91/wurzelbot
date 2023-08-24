from enum import Enum, auto

from pydantic import BaseModel, ConfigDict, PositiveFloat, PositiveInt


class WimpOrigin(Enum):
    GARDEN = auto()
    BEES_FARM = auto()


class Wimp(BaseModel):
    id: PositiveInt
    product_amount: dict
    reward: PositiveFloat
    origin: WimpOrigin
    model_config = ConfigDict(frozen=True, validate_assignment=True)
