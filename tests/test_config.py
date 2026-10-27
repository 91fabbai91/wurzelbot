import pytest
from pydantic import ValidationError

from config import Logging, Login, SellOnMarketPlace, Settings, Tasks


def test_login_valid_and_invalid_server():
    login = Login(server=2, name="test", password="pw")
    assert login.server == 2
    assert login.name == "test"

    with pytest.raises(ValidationError):
        Login(server=0, name="test", password="pw")

    with pytest.raises(ValidationError, match="Server must be Integer"):
        Login(server=47, name="test", password="pw")


def test_logging_model():
    log_default = Logging()
    assert log_default.level == "INFO"
    assert log_default.filename is None

    log_custom = Logging(level="DEBUG", filename="bot.log")
    assert log_custom.level == "DEBUG"
    assert log_custom.filename == "bot.log"


def test_sell_on_marketplace_model():
    som = SellOnMarketPlace(min_stock=100)
    assert som.min_stock == 100

    with pytest.raises(ValidationError):
        SellOnMarketPlace(min_stock=0)


def test_tasks_defaults():
    tasks = Tasks()
    assert tasks.farm_town_park is True
    assert tasks.start_bees_tour is True
    assert tasks.grow_for_quests == []
    assert tasks.grow_plants == []
    assert tasks.blacklisted_plants == set()
    assert tasks.sell_to_wimps_percentage is None


def test_tasks_percentage_validator():
    tasks_1 = Tasks(sell_to_wimps_percentage=1)
    assert tasks_1.sell_to_wimps_percentage == 1

    tasks_100 = Tasks(sell_to_wimps_percentage=100)
    assert tasks_100.sell_to_wimps_percentage == 100

    # 0 fails PositiveInt
    with pytest.raises(ValidationError):
        Tasks(sell_to_wimps_percentage=0)

    # > 100 fails custom percentage validator
    with pytest.raises(ValidationError, match="is not a percentage value"):
        Tasks(sell_to_wimps_percentage=101)


def test_tasks_quest_and_plants_validator():
    tasks = Tasks(
        grow_for_quests=["Salat", "Möhre", "Salat", "Gurke"],
        grow_plants=["Kürbis", "Kürbis", "Radieschen"],
    )
    # Deduplicated list preserving order
    assert tasks.grow_for_quests == ["Salat", "Möhre", "Gurke"]
    assert tasks.grow_plants == ["Kürbis", "Radieschen"]


def test_settings_instantiation():
    login = Login(server=1, name="bot", password="pw")
    logging_cfg = Logging()
    tasks = Tasks()
    settings = Settings(
        logins=login,
        logging=logging_cfg,
        tasks=tasks,
    )
    assert settings.logins.server == 1
    assert settings.product_information_filename == "product_names.json"
