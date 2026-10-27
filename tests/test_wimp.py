import pytest
from pydantic import ValidationError
from wimp import Wimp, WimpOrigin


def test_wimp_origin_enum():
    assert WimpOrigin.GARDEN is not None
    assert WimpOrigin.BEES_FARM is not None
    assert WimpOrigin.GARDEN != WimpOrigin.BEES_FARM


def test_wimp_creation_and_attributes():
    w = Wimp(
        id=1,
        product_amount={"1": 10, "2": 5},
        reward=25.5,
        origin=WimpOrigin.GARDEN,
        marketprice_percentage=120,
    )
    assert w.id == 1
    assert w.product_amount == {"1": 10, "2": 5}
    assert w.reward == 25.5
    assert w.origin == WimpOrigin.GARDEN
    assert w.marketprice_percentage == 120


def test_wimp_default_marketprice_percentage():
    w = Wimp(
        id=2,
        product_amount={"1": 3},
        reward=5.0,
        origin=WimpOrigin.BEES_FARM,
    )
    assert w.marketprice_percentage == 1


def test_wimp_is_profitable():
    w = Wimp(
        id=1,
        product_amount={"1": 10},
        reward=100.0,
        origin=WimpOrigin.GARDEN,
        marketprice_percentage=100,
    )
    assert w.is_profitable(80) is True
    assert w.is_profitable(100) is True
    assert w.is_profitable(101) is False


def test_wimp_validation_error():
    with pytest.raises(ValidationError):
        # negative id
        Wimp(
            id=-1,
            product_amount={"1": 10},
            reward=10.0,
            origin=WimpOrigin.GARDEN,
        )

    with pytest.raises(ValidationError):
        # negative reward
        Wimp(
            id=1,
            product_amount={"1": 10},
            reward=-5.0,
            origin=WimpOrigin.GARDEN,
        )
