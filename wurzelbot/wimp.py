from enum import Enum, auto
from typing import Optional

from pydantic import BaseModel, ConfigDict, PositiveFloat, PositiveInt


class WimpOrigin(Enum):
    GARDEN = auto()
    BEES_FARM = auto()


class Wimp(BaseModel):
    id: PositiveInt
    product_amount: dict
    reward: PositiveFloat
    origin: WimpOrigin
    marketprice_percentage: Optional[PositiveInt]
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    def is_profitable(self, percentage):
        return bool(self.marketprice_percentage >= percentage)
