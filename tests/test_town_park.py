from town_park import BlockedFieldType, TownPark


def test_blocked_field_type_enum():
    assert BlockedFieldType.WEED.id == 1
    assert BlockedFieldType.WEED.costs == 1000
    assert BlockedFieldType.TREE_STUMP.id == 2
    assert BlockedFieldType.TREE_STUMP.costs == 10000
    assert BlockedFieldType.STONE.id == 3
    assert BlockedFieldType.STONE.costs == 30000


def test_town_park_init_and_collect_cash(mock_http):
    mock_http.execute_command.side_effect = [
        # park_init
        {"data": {"data": {"points": 50000}}},
        # park_init inside collect_cash_points_from_park
        {"data": {"data": {"points": 50000}}},
        # park_clearcashpoint
        {"data": {"data": {"cashpoint": 250}}},
    ]

    tp = TownPark(mock_http, park_id=1)
    assert tp.id == 1
    cash = tp.collect_cash_points_from_park()
    assert cash == 250


def test_town_park_get_blocked_fields(mock_http):
    park_ground = {
        "1": {"item": "trash1"},  # WEED (1)
        "2": {"item": "trash2"},  # TREE_STUMP (2)
        "3": {"item": "normal_tile"},
        "4": {"item": "trash99"},  # Not in BlockedFieldType
    }
    mock_http.execute_command.side_effect = [
        # __init__
        {"data": {"data": {"points": 20000}}},
        # get_blocked_fields -> __go_to_park
        {"data": {"data": {"park": {"1": {"ground": park_ground}}}}},
    ]

    tp = TownPark(mock_http, park_id=1)
    blocked = tp.get_blocked_fields()
    assert blocked == {1: 1, 2: 2}


def test_town_park_destroy_weed_fields(mock_http):
    park_ground = {
        "1": {"item": "trash1"},  # WEED costs 1000
        "2": {"item": "trash2"},  # TREE_STUMP costs 10000
    }
    mock_http.execute_command.side_effect = [
        # __init__ with 5000 points (enough for weed, not stump)
        {"data": {"data": {"points": 5000}}},
        # get_blocked_fields
        {"data": {"data": {"park": {"1": {"ground": park_ground}}}}},
        # remove_blocked_field (tile 1)
        {"status": "ok"},
    ]

    tp = TownPark(mock_http, park_id=1)
    freed = tp.destroy_weed_fields()
    assert freed == 1


def test_town_park_renew_items_and_buy(mock_http):
    park_items = {
        "item_1": {"remain": -10},  # needs renew
        "item_2": {"remain": 500},  # still active
    }
    mock_http.execute_command.side_effect = [
        # __init__
        {"data": {"data": {"points": 1000}}},
        # renew_all_items_in_park -> __get_renewable_deko_from_park
        {"data": {"data": {"park": {"1": {"items": park_items}}}}},
        # __renew_items_in_park
        {"status": "ok"},
        # remove_blocked_field
        {"status": "ok"},
        # buy_new_item
        {"status": "ok"},
    ]

    tp = TownPark(mock_http, park_id=1)
    tp.renew_all_items_in_park()
    tp.remove_blocked_field(5)
    tp.buy_new_item("bench", 2)
    assert mock_http.execute_command.call_count >= 5
