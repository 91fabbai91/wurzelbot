from unittest.mock import patch

from garden import (
    AquaGarden,
    BlockedFieldType,
    Garden,
    find_blocked_fields_from_json_content,
    find_empty_fields_from_json_content,
)
from wimp import WimpOrigin


def test_garden_blocked_field_type():
    assert BlockedFieldType.WEED.id == 41
    assert BlockedFieldType.WEED.costs == 2.5
    assert BlockedFieldType.TREE_STUMP.id == 42
    assert BlockedFieldType.TREE_STUMP.costs == 250.0
    assert BlockedFieldType.STONE.id == 43
    assert BlockedFieldType.STONE.costs == 50.0
    assert BlockedFieldType.MOLE.id == 45
    assert BlockedFieldType.MOLE.costs == 500.0


def test_find_empty_and_blocked_fields(sample_garden_json):
    empty = find_empty_fields_from_json_content(sample_garden_json)
    # Field 1 has plant, field 2 is weed, field 3 is stone. Fields 4..204 are 0 (empty).
    assert 1 not in empty
    assert 2 not in empty
    assert 3 not in empty
    assert 4 in empty
    assert len(empty) == 201

    blocked = find_blocked_fields_from_json_content(sample_garden_json)
    assert blocked[2] == 41
    assert blocked[3] == 43
    assert 1 not in blocked


def test_garden_init_and_properties(mock_http, sample_garden_json):
    mock_http.execute_command.return_value = sample_garden_json
    g = Garden(mock_http, garden_id=1)

    assert g.id == 1
    assert g.len_x == 17
    assert g.len_y == 12
    assert g.number_of_fields == 204
    assert len(g.fields) == 1
    assert g.number_planted_plants(1) == 1
    assert g.number_planted_plants(2) == 0


def test_garden_get_fields_methods(mock_http, sample_garden_json):
    mock_http.execute_command.return_value = sample_garden_json
    g = Garden(mock_http, garden_id=1)

    empty = g.get_empty_fields()
    assert 4 in empty

    blocked = g.get_blocked_fields()
    assert blocked[2] == 41


def test_garden_destroy_weed_fields(mock_http, sample_garden_json):
    mock_http.execute_command.return_value = sample_garden_json
    mock_http.destroy_weed_field.return_value = {"status": "ok"}
    g = Garden(mock_http, garden_id=1)

    # Cash 10.0: enough for WEED (2.5), not enough for STONE (50.0)
    freed = g.destroy_weed_fields(cash=10.0)
    assert freed == 1
    mock_http.destroy_weed_field.assert_called_with(2)


def test_garden_harvest(mock_http, sample_garden_json):
    mock_http.execute_command.return_value = sample_garden_json
    g = Garden(mock_http, garden_id=1)
    g.harvest()
    assert mock_http.execute_command.call_count >= 2


def test_garden_grow_plants(mock_http, sample_garden_json, sample_product):
    mock_http.execute_command.return_value = sample_garden_json
    mock_http.grow_plant.return_value = {"status": "ok"}
    g = Garden(mock_http, garden_id=1)

    planted = g.grow_plants(sample_product, s_x=1, s_y=1, amount=3)
    assert planted == 3
    assert mock_http.grow_plant.call_count == 3


def test_garden_water_plants(mock_http, sample_garden_json):
    mock_http.execute_command.return_value = sample_garden_json
    mock_http.water_plant.return_value = {"status": "ok"}
    g = Garden(mock_http, garden_id=1)

    with patch("time.time", return_value=1700000000.0):
        g.water_plants()
    assert mock_http.water_plant.call_count >= 1


def test_garden_get_wimps_data(mock_http, sample_garden_json):
    mock_http.execute_command.return_value = sample_garden_json
    mock_http.execute_wimp_command.return_value = {
        "wimps": [
            {
                "sheet": {
                    "id": 101,
                    "sum": 50.0,
                    "products": [{"pid": 1, "amount": 10}],
                }
            }
        ]
    }
    g = Garden(mock_http, garden_id=1)
    wimps = g.get_wimps_data()
    assert len(wimps) == 1
    wimp = wimps[0]
    assert wimp.id == 101
    assert wimp.reward == 50.0
    assert wimp.origin == WimpOrigin.GARDEN
    assert wimp.product_amount == {"1": 10}


def test_aqua_garden(mock_http, sample_garden_json):
    mock_http.execute_command.return_value = sample_garden_json
    mock_http.getPlantsToWaterInAquaGarden.return_value = sample_garden_json
    ag = AquaGarden(mock_http)
    assert ag.id == 101

    ag.harvest()
    mock_http.execute_command.assert_called_with("do=watergardenHarvestAll")

    with patch("time.time", return_value=1700000000.0):
        ag.water_plants()
    assert mock_http.waterPlantInAquaGarden.call_count >= 1
