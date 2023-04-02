import os
from typing import Set
from pydantic import BaseSettings, BaseModel

class Login(BaseModel):
    server: int
    name: str
    password: str

class Logging(BaseModel):
    level: str
    filename: str

class SellOnMarketPlace(BaseModel):
    enabled: bool = False
    min_stock: int

class Tasks(BaseModel):
    grow_for_quests: Set[str] = set()
    sell_to_wimps_percentage: int
    sell_on_marketplace: SellOnMarketPlace
    farm_town_park: bool = True
    start_bees_tour: bool = True
    grow_plants: Set[str] = set()





class Settings(BaseSettings):
    logins: Login
    logging: Logging
    tasks: Tasks
    class Config:
        env_file = os.path.expanduser('config/.env')
        env_nested_delimiter = "__"
        env_file_encoding = 'utf-8'
