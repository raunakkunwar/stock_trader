import math
import time
from typing import TypedDict, Optional
from models.stock import Stock
from models.portfolio import Portfolio
from models.transaction import Transaction
from patterns.trade_controller import TradeController
from patterns.trade_processor import TradeProcessor
from services.research_service import ResearchService
from services.display_service import DisplayService
from services.market_simulator import MarketSimulator
from config import BUY_LIMIT


class IncrementalState(TypedDict):
    watchlist: dict
    portfolio: Portfolio
    ratings: dict
    picked_stock: Optional[str]
    picked_action: Optional[str]
    trade_result: Optional[Transaction]
    message: str
    mode: str
    display: DisplayService
    # Incremental-specific fields
    remaining_shares: int
    total_shares: int
    increment_step: int
    continue_trading: bool
    price_at_start: float
    market_simulator: MarketSimulator


def research_node(state: IncrementalState) -> dict:
    """Same research as conventional."""
    watchlist = state["watchlist"]
    portfolio = state["portfolio"]
    mode = state["mode"]
    display = state["display"]
    current_prices = {t: s.price for t, s in watchlist.items()}

    if mode == "ai":
        research = ResearchService()
        ratings, picked, action = research.evaluate(watchlist, portfolio, current_prices)
    else:
        display.console.print(display.show_watchlist(watchlist))
        display.console.print(display.show_portfolio(portfolio, current_prices))
        ratings = {}
        for ticker, stock in watchlist.items():
            change = stock.change_pct
            if change > 2.0:
                ratings[ticker] = "BUY"
            elif change < -2.0:
                ratings[ticker] = "SELL"
            else:
                ratings[ticker] = "HOLD"
        display.console.print(display.show_research(ratings, None, None))
        picked, action = display.prompt_stock_selection(watchlist, portfolio)

    # Calculate total shares for the trade
    total_shares = 0
    price_at_start = 0.0
    if picked:
        stock = watchlist[picked]
        price_at_start = stock.price
        if action == "BUY":
            total_shares = max(1, math.floor(BUY_LIMIT / stock.price))
        else:  # SELL
            position = portfolio.get_position(picked)
            total_shares = position.shares if position else 0

    msg = f"Research complete. Pick: {action} {picked}" if picked else "No pick this round."
    return {
        "ratings": ratings,
        "picked_stock": picked,
        "picked_action": action,
        "message": msg,
        "remaining_shares": total_shares,
        "total_shares": total_shares,
        "increment_step": 0,
        "continue_trading": True,
        "price_at_start": price_at_start,
    }


def should_trade(state: IncrementalState) -> str:
    if state["picked_stock"] is None:
        return "end"
    return "trade"


def incremental_trade_node(state: IncrementalState) -> dict:
    """Buy/sell only 1/3 of shares per step."""
    watchlist = state["watchlist"]
    portfolio = state["portfolio"]
    ticker = state["picked_stock"]
    action = state["picked_action"]
    remaining = state["remaining_shares"]
    step = state["increment_step"]
    total = state["total_shares"]
    display = state["display"]
    stock = watchlist[ticker]
    current_prices = {t: s.price for t, s in watchlist.items()}

    # Calculate 1/3 of remaining shares (at least 1)
    increment = max(1, math.ceil(total / 3))
    shares_this_step = min(increment, remaining)

    if shares_this_step <= 0:
        return {
            "trade_result": None,
            "remaining_shares": 0,
            "increment_step": step + 1,
            "continue_trading": False,
            "message": "No shares remaining to trade.",
        }

    processor = TradeProcessor(portfolio.account, portfolio)
    controller = TradeController(processor)
    transaction = controller.submit_trade_order(
        ticker, stock.price, shares_this_step, action, current_prices
    )

    new_remaining = remaining - shares_this_step if transaction.status == "FILLED" else remaining

    # Show incremental step
    assessment = "[green]FILLED[/green]" if transaction.status == "FILLED" else "[red]REJECTED[/red]"
    display.console.print(display.show_incremental_step(step + 1, shares_this_step, total, assessment))

    return {
        "trade_result": transaction,
        "remaining_shares": new_remaining,
        "increment_step": step + 1,
        "message": f"Step {step + 1}: {action} {shares_this_step} shares of {ticker} — {transaction.status}",
    }


def assess_node(state: IncrementalState) -> dict:
    """Check if price moved favorably to decide whether to continue.
    - BUY: if price went up within 1% -> continue buying
    - SELL: if price went down -> continue selling
    - Otherwise -> stop
    Also simulates a small price tick between increments.
    """
    watchlist = state["watchlist"]
    ticker = state["picked_stock"]
    action = state["picked_action"]
    remaining = state["remaining_shares"]
    price_at_start = state["price_at_start"]
    market_sim = state["market_simulator"]

    if remaining <= 0:
        return {"continue_trading": False, "message": "All shares traded."}

    # Simulate a small price movement between increments
    market_sim.update_prices(watchlist)

    current_price = watchlist[ticker].price
    price_change_pct = ((current_price - price_at_start) / price_at_start) * 100

    if action == "BUY":
        # Continue if price went up but within 1%
        if 0 <= price_change_pct <= 1.0:
            return {"continue_trading": True, "message": f"Price moved +{price_change_pct:.2f}% — continuing BUY."}
        else:
            return {"continue_trading": False, "message": f"Price moved {price_change_pct:.2f}% — stopping BUY."}
    else:  # SELL
        # Continue if price went down (within 1%)
        if -1.0 <= price_change_pct <= 0:
            return {"continue_trading": True, "message": f"Price moved {price_change_pct:.2f}% — continuing SELL."}
        else:
            return {"continue_trading": False, "message": f"Price moved {price_change_pct:.2f}% — stopping SELL."}


def should_continue(state: IncrementalState) -> str:
    if state["continue_trading"] and state["remaining_shares"] > 0:
        return "continue"
    return "end"
