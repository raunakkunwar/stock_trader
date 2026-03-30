from abc import ABC, abstractmethod
from models.trade_order import TradeOrder


class OrderBuilder(ABC):
    """Builder pattern interface for constructing TradeOrder objects."""

    @abstractmethod
    def set_stock(self, ticker: str, price: float) -> "OrderBuilder":
        ...

    @abstractmethod
    def set_quantity(self, quantity: int) -> "OrderBuilder":
        ...

    @abstractmethod
    def set_side(self, side: str) -> "OrderBuilder":
        ...

    @abstractmethod
    def set_order_type(self, order_type: str) -> "OrderBuilder":
        ...

    @abstractmethod
    def build(self) -> TradeOrder:
        ...


class MarketOrderBuilder(OrderBuilder):
    """Concrete builder: builds market TradeOrder objects."""

    def __init__(self):
        self._ticker: str = ""
        self._price: float = 0.0
        self._quantity: int = 0
        self._side: str = "BUY"
        self._order_type: str = "MARKET"

    def set_stock(self, ticker: str, price: float) -> "MarketOrderBuilder":
        self._ticker = ticker
        self._price = price
        return self

    def set_quantity(self, quantity: int) -> "MarketOrderBuilder":
        self._quantity = quantity
        return self

    def set_side(self, side: str) -> "MarketOrderBuilder":
        self._side = side
        return self

    def set_order_type(self, order_type: str) -> "MarketOrderBuilder":
        self._order_type = order_type
        return self

    def build(self) -> TradeOrder:
        if not self._ticker or self._quantity <= 0:
            raise ValueError("Incomplete order: ticker and quantity required")
        return TradeOrder(
            ticker=self._ticker,
            quantity=self._quantity,
            side=self._side,
            price_at_order=self._price,
            order_type=self._order_type,
        )
