import pytest
from unittest.mock import MagicMock
from user import User, UserDataBuilder, UserData, get_user_data_from_json_content
from wimp import WimpOrigin


def test_user_data_builder_and_user_data(sample_user_data_dict):
    user_data = get_user_data_from_json_content(sample_user_data_dict)
    assert isinstance(user_data, UserData)
    assert user_data.level_number == 15
    assert user_data.level == "Maulwurfjäger"
    assert user_data.bar == 1234.56
    assert user_data.coins == 42
    assert user_data.points == 500000
    assert user_data.mail == 1
    assert user_data.contracts == 2
    assert user_data.time == 1600000000


def test_user_init(mock_http, sample_user_data_dict, sample_garden_json):
    sample_user_data_dict["levelnr"] = 19
    # Setup returns for User initialization
    mock_http.get_username_from_server.return_value = {
        "table": ["<tr><td>Spielername</td><td>SuperGärtner</td></tr>"]
    }
    mock_http.read_user_data_from_server.return_value = sample_user_data_dict
    mock_http.execute_command.side_effect = [
        # __init_gardens (statsGetStats)
        {"table": ["<tr><td>Gärten</td><td>2</td></tr>"]},
        # Garden 1 __init__
        sample_garden_json,
        # Garden 2 __init__
        sample_garden_json,
        # is_honey_farm_available (citymap_init)
        {"data": {"location": {"bees": {"bought": 1}}}},
        # is_town_park_available (citymap_init)
        {"data": {"location": {"park": {"bought": {"parkid": 1}}}}},
        # TownPark __init__ (park_init)
        {"data": {"data": {"points": 1000}}},
        # is_deco_garden_available (citymap_init)
        {"data": {"location": {"decogarden": {"bought": 1}}}},
    ]
    # is_aqua_garden_available
    mock_http.get_trophies.return_value = {
        "html": "trophy_54.png); gray class"
    }
    # is_mail_address_confirmed
    mock_http.get_user_profile.return_value = "Profil: Bestätigt"

    user = User(mock_http)
    assert user.username == "SuperGärtner"
    assert user.number_of_gardens == 2
    assert len(user.gardens) == 2
    assert user.honey_farm_available is True
    assert user.town_park_available is True
    assert user.town_park is not None
    assert user.town_park.id == 1
    assert user.deco_garden_available is True
    assert user.aqua_garden_available is True
    assert user.mail_address_confirmed is False


def test_user_properties_and_setters(mock_http, sample_user_data_dict, sample_garden_json):
    mock_http.get_username_from_server.return_value = {
        "table": ["<tr><td>Spielername</td><td>Max</td></tr>"]
    }
    mock_http.read_user_data_from_server.return_value = sample_user_data_dict
    mock_http.execute_command.side_effect = [
        {"table": ["<tr><td>Gärten</td><td>1</td></tr>"]},
        sample_garden_json,
        {"data": {"location": {"bees": {"bought": 0}}}},
        {"data": {"location": {"park": {"bought": 0}}}},
        {"data": {"location": {"decogarden": {"bought": 0}}}},
    ]
    mock_http.get_trophies.return_value = {"html": ""}
    mock_http.get_user_profile.return_value = ""

    user = User(mock_http)
    user.account_login = "acc123"
    assert user.account_login == "acc123"

    user.user_id = 999
    assert user.user_id == 999

    user.username = "NeuerName"
    assert user.username == "NeuerName"

    with pytest.raises(ValueError, match="TownPark now available yet"):
        _ = user.town_park

    with pytest.raises(ValueError, match="Wrong number of gardens provided"):
        user.number_of_gardens = 10


def test_user_daily_bonus(mock_http, sample_user_data_dict, sample_garden_json):
    mock_http.get_username_from_server.return_value = {
        "table": ["<tr><td>Spielername</td><td>Max</td></tr>"]
    }
    sample_user_data_dict["dailyloginbonus"] = {
        "data": {
            "rewards": {
                "1": {"money": 100},
                "2": {"points": 50},
            }
        }
    }
    mock_http.read_user_data_from_server.return_value = sample_user_data_dict
    mock_http.execute_command.side_effect = [
        {"table": ["<tr><td>Gärten</td><td>0</td></tr>"]},
        {"data": {"location": {"bees": {"bought": 0}}}},
        {"data": {"location": {"park": {"bought": 0}}}},
        {"data": {"location": {"decogarden": {"bought": 0}}}},
        # get_daily_login_bonus
        sample_user_data_dict,
        {"status": "ok"},
    ]
    mock_http.get_trophies.return_value = {"html": ""}
    mock_http.get_user_profile.return_value = ""

    user = User(mock_http)
    user.get_daily_login_bonus()
    assert mock_http.execute_command.call_count >= 5


def test_user_wimp_actions(mock_http, sample_user_data_dict, sample_garden_json):
    mock_http.get_username_from_server.return_value = {
        "table": ["<tr><td>Spielername</td><td>Max</td></tr>"]
    }
    mock_http.read_user_data_from_server.return_value = sample_user_data_dict
    mock_http.execute_command.side_effect = [
        {"table": ["<tr><td>Gärten</td><td>0</td></tr>"]},
        {"data": {"location": {"bees": {"bought": 0}}}},
        {"data": {"location": {"park": {"bought": 0}}}},
        {"data": {"location": {"decogarden": {"bought": 0}}}},
        # sell to bees wimp
        {"status": "ok", "sold": True},
        # decline bees wimp
        {"status": "ok", "declined": True},
    ]
    mock_http.get_trophies.return_value = {"html": ""}
    mock_http.get_user_profile.return_value = ""
    mock_http.execute_wimp_command.side_effect = [
        {"newProductCounts": {"1": 5}},
        {"action": "wimp_declined"},
    ]

    user = User(mock_http)

    # Garden wimp
    res_sell_garden = user.sell_products_to_wimp(1, WimpOrigin.GARDEN)
    assert res_sell_garden == {"1": 5}

    res_dec_garden = user.decline_wimp(1, WimpOrigin.GARDEN)
    assert res_dec_garden == "wimp_declined"

    # Bees farm wimp
    res_sell_bees = user.sell_products_to_wimp(2, WimpOrigin.BEES_FARM)
    assert res_sell_bees["sold"] is True

    res_dec_bees = user.decline_wimp(2, WimpOrigin.BEES_FARM)
    assert res_dec_bees["declined"] is True

    with pytest.raises(ValueError, match="Wrong Type of WimpOrigin"):
        user.sell_products_to_wimp(3, "INVALID")

    with pytest.raises(ValueError, match="Wrong Type of WimpOrigin"):
        user.decline_wimp(3, "INVALID")
