from dataclasses import dataclass

@dataclass
class TradeOrder:
    ticker: str
    quantity: int
    side: str            # "BUY" or "SELL"
    price_at_order: float
    order_type: str = "MARKET"

    @property
    def total(self) -> float:
        return self.quantity * self.price_at_order
