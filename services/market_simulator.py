import random
from models.stock import Stock
from config import PRICE_FLUCTUATION_RANGE


class MarketSimulator:
    """Simulates stock price movement.
    For each stock: generate random float between -5 and +5,
    representing -5% to +5% fluctuation, update the price."""

    def update_prices(self, watchlist: dict[str, Stock]) -> None:
        low, high = PRICE_FLUCTUATION_RANGE
        for ticker, stock in watchlist.items():
            pct_change = random.uniform(low, high)
            stock.previous_price = stock.price
            stock.price = round(stock.price * (1 + pct_change / 100), 2)
