from offer import Offer


def test_offer_default_values():
    offer = Offer()
    assert offer.product == ""
    assert offer.seller == ""
    assert offer.price == 0.0
    assert offer.amount == -1


def test_offer_custom_values():
    offer = Offer(
        product="Salat",
        seller="GartenFreund",
        price=0.25,
        amount=100,
    )
    assert offer.product == "Salat"
    assert offer.seller == "GartenFreund"
    assert offer.price == 0.25
    assert offer.amount == 100

