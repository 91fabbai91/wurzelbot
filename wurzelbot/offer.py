from pydantic.dataclasses import dataclass


@dataclass
class Offer:
    product: str = ""
    seller: str = ""
    price: float = 0.0
    amount: int = -1
