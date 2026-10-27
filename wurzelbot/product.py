from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PositiveFloat,
    StrictBool,
    StrictInt,
    StrictStr,
)


class Product(BaseModel):
    id: StrictInt = Field(default=None, frozen=True, strict=True)
    cat: StrictStr = Field(..., frozen=True)
    sx: StrictInt | None = Field(None, frozen=True)
    sy: StrictInt | None = Field(None, frozen=True)
    name: StrictStr = Field(..., frozen=True)
    lvl: StrictInt = Field(..., frozen=True)
    crop: StrictInt | None = Field(None, frozen=True)
    is_plantable: StrictBool | None = Field(None, frozen=True)
    time: StrictInt | None = Field(None, frozen=True)
    price_npc: PositiveFloat | None = None
    model_config = ConfigDict(validate_assignment=True)

    def is_plant(self):
        return self.cat == "v"

    def is_decoration(self):
        return self.cat == "d"

    def getName(self):
        return self.name
