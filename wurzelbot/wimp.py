from pydantic import BaseModel, ConfigDict, PositiveFloat, PositiveInt


class Wimp(BaseModel):
    id: PositiveInt
    product_amount: dict
    reward: PositiveFloat
    model_config = ConfigDict(frozen=True, validate_assignment=True)
