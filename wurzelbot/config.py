import os
from typing import Set, Optional
from pydantic import BaseSettings, BaseModel, SecretStr

class Login(BaseSettings):
    server: int
    name: str
    password: SecretStr
    class Config:
        secrets_dir = '/run/secrets/login'

class Logging(BaseModel):
    level: str = "INFO"
    filename: Optional[str]

class SellOnMarketPlace(BaseModel):
    enabled: bool = False
    min_stock: int

class Tasks(BaseModel):
    grow_for_quests: Optional[Set[str]] = set()
    sell_to_wimps_percentage: int
    sell_on_marketplace: SellOnMarketPlace
    farm_town_park: bool = True
    start_bees_tour: bool = True
    grow_plants: Optional[Set[str]] = set()

class Settings(BaseSettings):
    logins: Login
    logging: Logging
    tasks: Tasks
    class Config:
        env_file = os.path.expanduser('config/.env')
        env_nested_delimiter = "__"
        env_file_encoding = 'utf-8'
        secrets_dir = '/run/secrets'
