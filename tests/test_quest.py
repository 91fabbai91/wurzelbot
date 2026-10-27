from unittest.mock import MagicMock

import pytest
from quest import (
    BeesGardenQuest,
    CityQuest,
    DecoGardenQuest,
    ParkQuest,
    Quest,
    QuestError,
    TreeQuest,
)


def test_abstract_quest(mock_http):
    class ConcreteQuest(Quest):
        pass

    q = ConcreteQuest(mock_http)
    with pytest.raises(NotImplementedError):
        q.get_quest()
    with pytest.raises(NotImplementedError):
        q.fulfill_quest()


def test_city_quest(mock_http):
    mock_http.execute_command.return_value = {
        "data": {
            "questtext": "Liefere 100 Salat und 50 Möhre f&uuml;r 120 wT und 50 Punkte."
        }
    }
    cq = CityQuest(mock_http)
    amount, reward = cq.get_quest()
    assert amount["Salat"] == 100
    assert amount["Möhre"] == 50
    assert "120 wT" in reward
    assert "50 Punkte" in reward

    # fulfill_quest
    cq.fulfill_quest()
    assert mock_http.execute_command.call_count >= 2


def test_city_quest_error(mock_http):
    mock_http.execute_command.side_effect = Exception("Network error")
    cq = CityQuest(mock_http)
    with pytest.raises(QuestError, match="No CityQuest available"):
        cq.get_quest()


def test_park_quest(mock_http):
    quest_payload = {
        "questData": {
            "questnr": 5,
            "reward": ["100 Punkte"],
            "products": [
                {"name": "Salat", "pid": 1, "missing": 20},
                {"name": "Möhre", "pid": 2, "missing": 10},
            ],
        }
    }
    mock_http.execute_command.return_value = quest_payload
    pq = ParkQuest(mock_http)
    amount, reward = pq.get_quest()
    assert amount["Salat"] == 20
    assert amount["Möhre"] == 10
    assert reward == ["100 Punkte"]

    pq.fulfill_quest()
    # Called execute_command for get_quest + 2 products
    assert mock_http.execute_command.call_count >= 3


def test_park_quest_error(mock_http):
    mock_http.execute_command.side_effect = Exception("No quest")
    pq = ParkQuest(mock_http)
    with pytest.raises(QuestError, match="No ParkQuest available"):
        pq.get_quest()


def test_deco_garden_quest(mock_http):
    garden_objects = {"1": {"id": 101}}
    click_result = {
        "quest_data": {
            "questnr": 1,
            "reward": "50 Punkte",
            "products": [
                {"name": "Salat", "pid": 1, "missing": 15},
            ],
        }
    }
    mock_http.execute_decogarden_command.side_effect = [
        {"objects": garden_objects},
        click_result,
    ]
    dq = DecoGardenQuest(mock_http)
    amount, reward = dq.get_quest()
    assert amount["Salat"] == 15
    assert "50 Punkte" in reward

    # fulfill_quest
    mock_http.execute_decogarden_command.side_effect = [
        {"objects": [{"id": 101}]},
        {"questData": {"questnr": 1, "products": [{"pid": 1, "missing": 15}]}},
        {"status": "ok"},
    ]
    dq.fulfill_quest()


def test_deco_garden_quest_error(mock_http):
    mock_http.execute_decogarden_command.side_effect = Exception("Deco error")
    dq = DecoGardenQuest(mock_http)
    with pytest.raises(QuestError, match="No DecoGardenQuest available"):
        dq.get_quest()


def test_bees_garden_quest(mock_http):
    mock_http.execute_command.return_value = {
        "questnr": 3,
        "questData": {
            "reward": "Honigkuchen",
            "products": [{"name": "Klee", "pid": 10, "missing": 30}],
        },
    }
    bq = BeesGardenQuest(mock_http)
    amount, reward = bq.get_quest()
    assert amount["Klee"] == 30
    assert reward == "Honigkuchen"

    bq.fulfill_quest()
    assert mock_http.execute_command.call_count >= 2


def test_bees_garden_quest_error(mock_http):
    mock_http.execute_command.side_effect = Exception("Bees error")
    bq = BeesGardenQuest(mock_http)
    with pytest.raises(QuestError, match="No BeesGardenQuest available"):
        bq.get_quest()


def test_tree_quest(mock_http):
    mock_http.execute_tree_gardencommand.return_value = {
        "quests": {
            "1": {
                "rewardtext": "<b>Belohnung: 200 Punkte</b>",
                "short_text": "Liefere 10 Apfel und 5 Birne.",
            }
        }
    }
    tq = TreeQuest(mock_http)
    amount, reward = tq.get_quest()
    assert amount["Apfel"] == 10
    assert amount["Birne"] == 5
    assert "200 Punkte" in reward

    with pytest.raises(NotImplementedError):
        tq.fulfill_quest()


def test_tree_quest_error(mock_http):
    mock_http.execute_tree_gardencommand.side_effect = Exception("Tree error")
    tq = TreeQuest(mock_http)
    with pytest.raises(QuestError, match="No TreeQuest available"):
        tq.get_quest()


def test_quest_error_str():
    err = QuestError("Failed")
    assert str(err) == "'Failed'"
