from enum import Enum, auto
from typing import Optional

from pydantic import BaseModel, ConfigDict, NonNegativeInt, PositiveFloat


class WimpOrigin(Enum):
    GARDEN = auto()
    BEES_FARM = auto()


class Wimp(BaseModel):
    id: NonNegativeInt
    product_amount: dict
    reward: PositiveFloat
    origin: WimpOrigin
    marketprice_percentage: Optional[NonNegativeInt] = 1
    model_config = ConfigDict(frozen=False, validate_assignment=True)

    def is_profitable(self, percentage):
        return bool(self.marketprice_percentage >= percentage)
