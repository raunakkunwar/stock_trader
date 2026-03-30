from models.trade_order import TradeOrder
from models.transaction import Transaction
from .order_builder import MarketOrderBuilder
from .trade_processor import TradeProcessor


class TradeController:
    """Controller pattern: receives requests from the UI (terminal),
    delegates to OrderBuilder and TradeProcessor.
    Does NOT contain business logic itself."""

    def __init__(self, trade_processor: TradeProcessor):
        self.trade_processor = trade_processor
        self.order_builder = MarketOrderBuilder()

    def submit_trade_order(self, ticker: str, price: float, quantity: int,
                           side: str, current_prices: dict) -> Transaction:
        """Full design sequence:
        1. Use OrderBuilder to construct TradeOrder (Builder pattern)
        2. Delegate to TradeProcessor to process (Creator + Expert patterns)
        """
        # Builder pattern: construct the TradeOrder step by step
        trade_order = (
            self.order_builder
            .set_stock(ticker, price)
            .set_quantity(quantity)
            .set_side(side)
            .set_order_type("MARKET")
            .build()
        )

        # Reset builder for next use
        self.order_builder = MarketOrderBuilder()

        # Delegate to TradeProcessor
        return self.trade_processor.process(trade_order, current_prices)
