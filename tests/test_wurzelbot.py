import pytest
from unittest.mock import MagicMock, patch
from wurzelbot import Wurzelbot, NotStartedException
from login_data import LoginData
from product import Product
from wimp import Wimp, WimpOrigin
import quest


def test_not_started_exception_guards():
    bot = Wurzelbot()
    with pytest.raises(NotStartedException):
        bot.water_plants_in_all_gardens()

    with pytest.raises(NotStartedException):
        bot.get_empty_fields_of_gardens()

    with pytest.raises(NotStartedException):
        bot.has_empty_fields()

    with pytest.raises(NotStartedException):
        bot.get_weed_fields_of_gardens()

    with pytest.raises(NotStartedException):
        bot.destroy_weed_field(1)

    with pytest.raises(NotStartedException):
        bot.harvest_all_garden()

    with pytest.raises(NotStartedException):
        bot.collect_cash_from_park()

    with pytest.raises(NotStartedException):
        bot.print_stock()

    with pytest.raises(NotStartedException):
        bot.get_ordered_stock_list()

    with pytest.raises(NotStartedException):
        bot.get_lowest_plant_stock_entry()

    with pytest.raises(NotStartedException):
        bot.renew_all_items_in_park()

    with pytest.raises(NotStartedException):
        bot.grow_plants_in_gardens(None)


def test_not_started_exception_str():
    exc = NotStartedException("Custom message")
    assert str(exc) == "'Custom message'"


@pytest.fixture
def running_bot():
    bot = Wurzelbot()
    bot._Wurzelbot__wurzelbot_started = True
    bot._Wurzelbot__http_connection = MagicMock()
    bot._Wurzelbot__user = MagicMock()
    bot._Wurzelbot__stock = MagicMock()
    bot._Wurzelbot__marketplace = MagicMock()
    bot._Wurzelbot__marketplace.MINIMAL_DISCOUNT = 0.01
    bot._Wurzelbot__marketplace.FEE_PERCENTAGE = 0.1
    bot._Wurzelbot__product_information = MagicMock()
    bot._Wurzelbot__messenger = MagicMock()
    bot._Wurzelbot__bees_farm = MagicMock()
    bot._Wurzelbot__notes = MagicMock()
    bot._Wurzelbot__city_quest = MagicMock()
    bot._Wurzelbot__park_quest = MagicMock()
    bot._Wurzelbot__deco_garden_quest = MagicMock()
    bot._Wurzelbot__bee_farm_quest = MagicMock()
    bot._Wurzelbot__tree_quest = MagicMock()
    bot._Wurzelbot__blacklisted_plants = set()
    return bot


def test_start_and_stop_wurzelbot(mock_http):
    bot = Wurzelbot()
    login = LoginData(server=1, username="testuser", password="secretpassword")

    bot._Wurzelbot__http_connection = mock_http

    with patch("user.User") as mock_user_cls, \
         patch("messenger.Messenger"), \
         patch("stock.Stock"), \
         patch("product_information.ProductInformation"), \
         patch("marketplace.Marketplace"), \
         patch("notes.Notes"):

        mock_user = mock_user_cls.return_value
        mock_user.is_honey_farm_available.return_value = True

        bot.start_wurzelbot(login, "product_names.json", blacklisted_plants={"Rose"})
        assert bot._Wurzelbot__wurzelbot_started is True
        mock_http.login.assert_called_with(login)

        bot.stop_wurzelbot()
        assert bot._Wurzelbot__wurzelbot_started is False
        mock_http.logout.assert_called_once()


def test_basic_delegations(running_bot):
    running_bot.start_all_bees_tour()
    running_bot._Wurzelbot__bees_farm.start_all_bees_tour.assert_called_once()

    running_bot.get_daily_login_bonus()
    running_bot._Wurzelbot__user.get_daily_login_bonus.assert_called_once()

    # Sell on market
    fake_prod = MagicMock(id=5)
    running_bot._Wurzelbot__product_information.get_product_by_name.return_value = fake_prod
    running_bot.sell_on_market("Salat", price=0.25, number=10)
    running_bot._Wurzelbot__marketplace.sell_on_market.assert_called_with(5, 0.25, 10)


def test_garden_actions(running_bot):
    mock_g1 = MagicMock()
    mock_g1.get_empty_fields.return_value = [1, 2]
    mock_g1.get_weed_fields.return_value = {3: 41}
    mock_g1.fields = [[1, 2, 0, 0]]
    running_bot._Wurzelbot__user.gardens = [mock_g1]

    # Water
    running_bot.water_plants_in_all_gardens()
    mock_g1.water_plants.assert_called_once()

    # Empty fields
    empty = running_bot.get_empty_fields_of_gardens()
    assert empty == [[1, 2]]
    assert running_bot.has_empty_fields() is True

    # Weed
    weeds = running_bot.get_weed_fields_of_gardens()
    assert weeds == [{3: 41}]

    running_bot.destroy_weed_field(3)
    running_bot._Wurzelbot__http_connection.destroy_weed_field.assert_called_with(3)

    # Harvest
    running_bot.harvest_all_garden()
    mock_g1.harvest.assert_called_once()
    running_bot._Wurzelbot__stock.update_number_in_stock.assert_called_once()

    # Plants in garden count
    counts = running_bot.number_of_plants_in_garden()
    assert counts == {2: 1}

    # Destroy weed in garden
    running_bot._Wurzelbot__user.user_data.bar = 100.0
    running_bot.destroy_weed_fields_in_garden()
    mock_g1.destroy_weed_fields.assert_called_with(100.0)


def test_park_actions(running_bot):
    running_bot.collect_cash_from_park()
    running_bot._Wurzelbot__user.town_park.collect_cash_points_from_park.assert_called_once()

    running_bot.renew_all_items_in_park()
    running_bot._Wurzelbot__user.town_park.renew_all_items_in_park.assert_called_once()

    running_bot.destroy_weed_fields_in_town_park()
    running_bot._Wurzelbot__user.town_park.destroy_weed_fields.assert_called_once()


def test_stock_printing_and_ordering(running_bot):
    fake_prod = MagicMock()
    fake_prod.getName.return_value = "Salat"
    fake_prod.is_plant.return_value = True
    fake_prod.is_plantable = True

    running_bot._Wurzelbot__stock.get_keys.return_value = ["1"]
    running_bot._Wurzelbot__stock.get_stock_by_product_id.return_value = 50
    running_bot._Wurzelbot__product_information.get_product_by_id.return_value = fake_prod

    running_bot.print_stock()

    # Ordered stock
    running_bot._Wurzelbot__stock.get_ordered_stock_list.return_value = {"1": {"amount": 50}}
    ordered_str = running_bot.get_ordered_stock_list()
    assert "Salat" in ordered_str
    assert "50" in ordered_str

    # Lowest stock
    lowest = running_bot.get_lowest_plant_stock_entry()
    assert lowest == "Salat"


def test_grow_plants_workflows(running_bot):
    fake_plant = Product(
        id=1,
        cat="v",
        name="Salat",
        lvl=1,
        sx=1,
        sy=1,
        is_plantable=True,
    )
    running_bot._Wurzelbot__product_information.get_product_by_name.return_value = fake_plant
    running_bot._Wurzelbot__product_information.get_product_by_id.return_value = fake_plant
    running_bot._Wurzelbot__stock.get_stock_by_product_id.return_value = 20

    mock_g = MagicMock()
    mock_g.id = 1
    mock_g.grow_plants.return_value = 10
    running_bot._Wurzelbot__user.gardens = [mock_g]

    # By name
    running_bot.grow_plants_in_gardens_by_name("Salat", amount=10)
    mock_g.grow_plants.assert_called_with(fake_plant, 1, 1, 10)

    # By id
    running_bot.grow_plants_in_gardens_by_id(1, amount=10)
    mock_g.grow_plants.assert_called_with(fake_plant, 1, 1, 10)

    # grow_anything
    running_bot._Wurzelbot__stock.get_ordered_stock_list.return_value = {"1": {"amount": 20}}
    running_bot.grow_anything()


def test_quests_workflows(running_bot):
    mock_city_quest = MagicMock()
    mock_city_quest.get_quest.return_value = ({"Salat": 100}, ["50 wT"])
    running_bot._Wurzelbot__city_quest = mock_city_quest

    fake_prod = Product(
        id=1,
        cat="v",
        name="Salat",
        lvl=1,
        crop=1,
        sx=1,
        sy=1,
        is_plantable=True,
    )
    running_bot._Wurzelbot__product_information.get_product_by_name.return_value = fake_prod
    running_bot._Wurzelbot__product_information.get_plural.return_value = "Salat"
    running_bot._Wurzelbot__stock.get_stock_by_product_id.return_value = 20
    running_bot._Wurzelbot__user.gardens = []

    missing = running_bot.get_missing_quest_amount(mock_city_quest)
    assert missing == {"Salat": 80}

    # plant_according_to_quest
    running_bot.plant_according_to_quest(quest.CityQuest.__name__)


def test_wimps_workflows(running_bot):
    wimp1 = Wimp(
        id=1,
        product_amount={"1": 5},
        reward=50.0,
        origin=WimpOrigin.GARDEN,
        marketprice_percentage=120,
    )
    mock_garden = MagicMock()
    mock_garden.get_wimps_data.return_value = [wimp1]
    running_bot._Wurzelbot__user.gardens = [mock_garden]
    running_bot._Wurzelbot__bees_farm = None
    running_bot._Wurzelbot__user.username = "Tester"

    fake_prod = Product(
        id=1,
        cat="v",
        name="Salat",
        lvl=1,
        crop=1,
        sx=1,
        sy=1,
        is_plantable=True,
        price_npc=0.16,
    )
    running_bot._Wurzelbot__product_information.get_product_by_id.return_value = fake_prod
    running_bot._Wurzelbot__marketplace.get_cheapest_offer.return_value = 0.20
    running_bot._Wurzelbot__stock.get_ordered_stock_list.return_value = {"1": {"amount": 50}}
    running_bot._Wurzelbot__stock.get_stock_by_product_id.return_value = 50
    running_bot._Wurzelbot__notes.get_min_stock.return_value = 10

    # get_wimps_data
    wimps = running_bot.get_wimps_data()
    assert len(wimps) == 1

    # check_wimps_required_amount: stock has 50, needed is 5 + max(10, 10, 0) = 15 -> True
    stock_dict = {"1": {"amount": 50}}
    assert running_bot.check_wimps_required_amount(0, {"1": 5}, stock_dict) is True

    # sell_wimps_products
    running_bot.sell_wimps_products(minimal_balance=0, percentage=100)
    running_bot._Wurzelbot__user.sell_products_to_wimp.assert_called_once()

    # plant_according_to_wimps
    running_bot.plant_according_to_wimps([wimp1], percentage=100)


def test_sell_on_marketplace_with_min_stock(running_bot):
    running_bot._Wurzelbot__user.user_data.bar = 500.0
    running_bot._Wurzelbot__user.username = "Tester"
    running_bot._Wurzelbot__notes.get_min_stock.return_value = 20
    running_bot._Wurzelbot__stock.get_ordered_stock_list.return_value = {
        "1": {"amount": 100, "name": "Salat"}
    }
    running_bot._Wurzelbot__marketplace.get_cheapest_offer.return_value = 0.20
    fake_prod = Product(
        id=1,
        cat="v",
        name="Salat",
        lvl=1,
        crop=1,
        price_npc=0.18,
    )
    running_bot._Wurzelbot__product_information.get_product_by_id.return_value = fake_prod

    running_bot.sell_on_marketplace_with_min_stock(minimal_balance=10)
    running_bot._Wurzelbot__marketplace.sell_on_market.assert_called_once()
