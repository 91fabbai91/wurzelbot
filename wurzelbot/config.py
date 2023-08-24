import os
from typing import FrozenSet, Optional

from pydantic import BaseModel, PositiveInt, SecretStr, StrictStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Login(BaseSettings):
    server: PositiveInt
    name: StrictStr
    password: SecretStr

    @field_validator("server")
    @classmethod
    def server_match(cls, server):
        if server < 0 or server > 46:
            raise ValueError(
                "Server must be Integer, greater than 0 and smaller than 47"
            )
        return server

    model_config = SettingsConfigDict(
        secrets_dir="/run/secrets/login", frozen=True, validate_assignment=True
    )


class Logging(BaseModel):
    level: StrictStr = "INFO"
    filename: Optional[StrictStr] = None


class SellOnMarketPlace(BaseModel):
    min_stock: PositiveInt


class Tasks(BaseModel):
    grow_for_quests: Optional[FrozenSet[StrictStr]] = set()
    sell_to_wimps_percentage: Optional[PositiveInt] = None
    sell_on_marketplace: Optional[SellOnMarketPlace] = None
    farm_town_park: bool = True
    start_bees_tour: bool = True
    grow_plants: Optional[FrozenSet[StrictStr]] = set()

    @field_validator("sell_to_wimps_percentage")
    @classmethod
    def percentage_validator(cls, percentage):
        if percentage < 0 or percentage > 100:
            raise ValueError(f"{percentage} is not a percentage value")
        return percentage


class Settings(BaseSettings):
    logins: Login
    logging: Logging
    tasks: Tasks
    model_config = SettingsConfigDict(
        env_file=os.path.expanduser("config/.env"),
        env_nested_delimiter="__",
        env_file_encoding="utf-8",
        secrets_dir="/run/secrets",
        frozen=True,
    )
