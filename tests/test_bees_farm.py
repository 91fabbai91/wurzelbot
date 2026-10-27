from unittest.mock import MagicMock

from bees_farm import BeesFarm, BeesTour
from wimp import WimpOrigin


def test_bees_tour_enum():
    assert BeesTour.TWO_HOURS_TOUR.value == 1
    assert BeesTour.EIGHT_HOURS_TOUR.value == 2
    assert BeesTour.TWENTYFOUR_HOURS_TOUR.value == 3


def test_bees_farm_init(mock_http):
    hives_data = {
        "1": {"time": 100, "level": 1, "pid": 1},
        "2": {"time": 200, "level": 3, "pid": 2},
        "3": {"level": 2},  # missing "time"
    }
    mock_http.execute_command.return_value = {"data": {"data": {"hives": hives_data}}}

    bf = BeesFarm(mock_http)
    # Sorted by level reverse: 2 (level 3) then 1 (level 1)
    assert list(bf.hives.keys()) == [2, 1]
    assert 3 not in bf.hives


def test_bees_farm_start_tours(mock_http):
    hives_data = {
        "1": {"time": 100, "level": 1, "tour_remain": -5},
        "2": {"time": 100, "level": 2, "tour_remain": 1200},  # currently flying
        "3": {"time": 100, "level": 1},  # no tour_remain
    }
    mock_http.execute_command.side_effect = [
        # __init__
        {"data": {"data": {"hives": hives_data}}},
        # start_bees_tour
        {"status": "ok"},
        # start_all_bees_tour -> __go_to_bees
        {
            "data": {
                "stock": {"honey": 100000},
                "data": {"hives": hives_data},
            }
        },
        # bees_fill
        {"status": "ok"},
        # start_bees_tour for hive 1
        {"status": "ok"},
        # start_bees_tour for hive 3
        {"status": "ok"},
    ]

    bf = BeesFarm(mock_http)
    bf.start_bees_tour(1, BeesTour.TWO_HOURS_TOUR)
    bf.start_all_bees_tour(BeesTour.TWO_HOURS_TOUR)
    assert mock_http.execute_command.call_count >= 5


def test_bees_farm_get_wimp_data(mock_http):
    wimps_raw = [
        {
            "id": 10,
            "price": 45.0,
            "data": {"1": "5", "2": "10"},
        }
    ]
    mock_http.execute_command.side_effect = [
        # __init__
        {"data": {"data": {"hives": {}}}},
        # get_wimp_data -> __go_to_bees
        {
            "data": {
                "wimps": wimps_raw,
                "data": {"hives": {}},
            }
        },
    ]

    bf = BeesFarm(mock_http)
    wimps = bf.get_wimp_data()
    assert len(wimps) == 1
    wimp = wimps[0]
    assert wimp.id == 10
    assert wimp.reward == 45.0
    assert wimp.origin == WimpOrigin.BEES_FARM
    assert wimp.product_amount == {"1": 5, "2": 10}


def test_bees_farm_change_products(mock_http):
    hives_data = {
        "1": {"time": 100, "level": 1, "pid": 1},
        "2": {"time": 100, "level": 1, "pid": 2},
    }
    mock_http.execute_command.side_effect = [
        # __init__
        {"data": {"data": {"hives": hives_data}}},
        # change hive 1
        {"status": "ok"},
    ]

    bf = BeesFarm(mock_http)
    bf.change_all_bee_hives_product(product_id=2)
    assert mock_http.execute_command.call_count >= 2
