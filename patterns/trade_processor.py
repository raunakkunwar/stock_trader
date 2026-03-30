from models.trade_order import TradeOrder
from models.transaction import Transaction
from models.account import Account
from models.portfolio import Portfolio


class TradeProcessor:
    """Creator pattern: TradeProcessor creates Transaction objects because it
    records/uses the trade data. Also uses Expert pattern by asking Account
    to verify funds (Account is the expert on fund sufficiency)."""

    def __init__(self, account: Account, portfolio: Portfolio):
        self.account = account
        self.portfolio = portfolio

    def process(self, trade_order: TradeOrder, current_prices: dict) -> Transaction:
        """Process a trade order through the full sequence:
        1. Verify funds/holdings via Account (Expert pattern)
        2. Execute the exchange (simulated)
        3. Create Transaction record (Creator pattern)
        4. Update Portfolio
        """
        if trade_order.side == "BUY":
            # Expert pattern: ask Account if funds are sufficient
            if not self.account.is_funds_sufficient(trade_order.total):
                return Transaction.create(trade_order, "REJECTED")

            # Check 10% holding limit
            if not self.portfolio.is_within_holding_limit(
                trade_order.ticker, trade_order.total, current_prices
            ):
                return Transaction.create(trade_order, "REJECTED")

            # Execute: debit account
            self.account.debit(trade_order.total)

        elif trade_order.side == "SELL":
            position = self.portfolio.get_position(trade_order.ticker)
            if position is None or position.shares < trade_order.quantity:
                return Transaction.create(trade_order, "REJECTED")

            # Execute: credit account
            self.account.credit(trade_order.total)

        # Creator pattern: TradeProcessor creates the Transaction
        transaction = Transaction.create(trade_order, "FILLED")

        # Update portfolio holdings
        self.portfolio.update_holdings(transaction)

        return transaction
