import math
from typing import TypedDict, Optional
from models.stock import Stock
from models.portfolio import Portfolio
from models.transaction import Transaction
from patterns.trade_controller import TradeController
from patterns.trade_processor import TradeProcessor
from services.research_service import ResearchService
from services.display_service import DisplayService
from config import BUY_LIMIT


class TradingState(TypedDict):
    watchlist: dict
    portfolio: Portfolio
    ratings: dict
    picked_stock: Optional[str]
    picked_action: Optional[str]
    trade_result: Optional[Transaction]
    message: str
    mode: str
    display: DisplayService


def research_node(state: TradingState) -> dict:
    """Evaluate all stocks, generate ratings, pick ONE stock (or none)."""
    watchlist = state["watchlist"]
    portfolio = state["portfolio"]
    mode = state["mode"]
    display = state["display"]
    current_prices = {t: s.price for t, s in watchlist.items()}

    if mode == "ai":
        research = ResearchService()
        ratings, picked, action = research.evaluate(watchlist, portfolio, current_prices)
    else:
        # Manual mode: show stocks and prompt user
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

    msg = f"Research complete. Pick: {action} {picked}" if picked else "No pick this round."
    return {
        "ratings": ratings,
        "picked_stock": picked,
        "picked_action": action,
        "message": msg,
    }


def should_trade(state: TradingState) -> str:
    """Conditional edge: if picked_stock is None -> END, else -> trade."""
    if state["picked_stock"] is None:
        return "end"
    return "trade"


def trade_node(state: TradingState) -> dict:
    """Execute buy ($5,000) or sell (all shares) using the full design sequence."""
    watchlist = state["watchlist"]
    portfolio = state["portfolio"]
    ticker = state["picked_stock"]
    action = state["picked_action"]
    stock = watchlist[ticker]
    current_prices = {t: s.price for t, s in watchlist.items()}

    processor = TradeProcessor(portfolio.account, portfolio)
    controller = TradeController(processor)

    if action == "BUY":
        quantity = max(1, math.floor(BUY_LIMIT / stock.price))
        transaction = controller.submit_trade_order(
            ticker, stock.price, quantity, "BUY", current_prices
        )
    else:  # SELL
        position = portfolio.get_position(ticker)
        if position and position.shares > 0:
            transaction = controller.submit_trade_order(
                ticker, stock.price, position.shares, "SELL", current_prices
            )
        else:
            from models.trade_order import TradeOrder
            dummy_order = TradeOrder(ticker, 0, "SELL", stock.price)
            transaction = Transaction.create(dummy_order, "REJECTED")

    return {
        "trade_result": transaction,
        "message": f"Trade {transaction.status}: {action} {ticker}",
    }


def update_portfolio_node(state: TradingState) -> dict:
    """Update portfolio and balance — already done in TradeProcessor.process()."""
    transaction = state["trade_result"]
    if transaction and transaction.status == "FILLED":
        return {"message": f"Portfolio updated: {transaction.trade_order.side} {transaction.trade_order.ticker}"}
    return {"message": "No portfolio update needed."}
