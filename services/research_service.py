from models.stock import Stock
from models.portfolio import Portfolio
from config import BUY_LIMIT


class ResearchService:
    """AI-automated research: evaluates stocks and picks one."""

    def evaluate(self, watchlist: dict[str, Stock], portfolio: Portfolio,
                 current_prices: dict) -> tuple[dict, str | None, str | None]:
        """
        Returns:
          - ratings: {ticker: "BUY"/"SELL"/"HOLD"}
          - picked_ticker: str or None
          - picked_action: "BUY" or "SELL" or None

        Rating logic (simulated AI):
          - If price went up > 2%: BUY
          - If price went down > 2%: SELL
          - Otherwise: HOLD
          - From all BUY/SELL candidates, pick the one with strongest movement
          - Check constraints before picking:
            - BUY: balance >= $5,000 AND stock won't exceed 10% of portfolio
            - SELL: must own the stock
        """
        ratings = {}
        candidates = []

        for ticker, stock in watchlist.items():
            change = stock.change_pct
            if change > 2.0:
                ratings[ticker] = "BUY"
                candidates.append((ticker, "BUY", abs(change)))
            elif change < -2.0:
                ratings[ticker] = "SELL"
                candidates.append((ticker, "SELL", abs(change)))
            else:
                ratings[ticker] = "HOLD"

        # Sort by strength of movement (descending)
        candidates.sort(key=lambda x: x[2], reverse=True)

        # Pick the best valid candidate
        for ticker, action, strength in candidates:
            if action == "BUY":
                # Check funds
                if not portfolio.account.is_funds_sufficient(BUY_LIMIT):
                    continue
                # Check 10% holding limit
                price = watchlist[ticker].price
                if not portfolio.is_within_holding_limit(ticker, BUY_LIMIT, current_prices):
                    continue
                return ratings, ticker, action
            elif action == "SELL":
                # Must own the stock
                pos = portfolio.get_position(ticker)
                if pos is None or pos.shares <= 0:
                    continue
                return ratings, ticker, action

        return ratings, None, None
