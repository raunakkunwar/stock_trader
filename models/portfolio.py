from dataclasses import dataclass, field
from .account import Account
from .transaction import Transaction

@dataclass
class PortfolioPosition:
    shares: int
    avg_cost: float

    @property
    def total_cost(self) -> float:
        return self.shares * self.avg_cost

class Portfolio:
    def __init__(self, account: Account):
        self.account = account
        self.holdings: dict[str, PortfolioPosition] = {}

    def update_holdings(self, transaction: Transaction) -> None:
        order = transaction.trade_order
        if transaction.status != "FILLED":
            return
        ticker = order.ticker
        if order.side == "BUY":
            if ticker in self.holdings:
                pos = self.holdings[ticker]
                total_cost = pos.shares * pos.avg_cost + order.quantity * order.price_at_order
                total_shares = pos.shares + order.quantity
                pos.avg_cost = total_cost / total_shares
                pos.shares = total_shares
            else:
                self.holdings[ticker] = PortfolioPosition(
                    shares=order.quantity,
                    avg_cost=order.price_at_order,
                )
        elif order.side == "SELL":
            if ticker in self.holdings:
                self.holdings[ticker].shares -= order.quantity
                if self.holdings[ticker].shares <= 0:
                    del self.holdings[ticker]

    def get_total_market_value(self, current_prices: dict) -> float:
        total = self.account.balance
        for ticker, pos in self.holdings.items():
            price = current_prices.get(ticker, pos.avg_cost)
            total += pos.shares * price
        return total

    def is_within_holding_limit(self, ticker: str, additional_value: float, current_prices: dict) -> bool:
        """Check 10% max holding constraint."""
        from config import MAX_HOLDING_PCT
        total_portfolio = self.get_total_market_value(current_prices)
        current_holding = 0.0
        if ticker in self.holdings:
            price = current_prices.get(ticker, self.holdings[ticker].avg_cost)
            current_holding = self.holdings[ticker].shares * price
        return (current_holding + additional_value) <= total_portfolio * MAX_HOLDING_PCT

    def get_position(self, ticker: str):
        return self.holdings.get(ticker, None)
