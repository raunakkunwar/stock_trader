# UC3 Stock Trading Simulator — Architecture & Implementation Guide

## Overview

Build a **Python terminal app** using `rich` for colorful UI and `langgraph` for state machine graphs. The app simulates stock trading with two processes (conventional + iterative incremental) and two methods (AI-automated + manual).

---

## Project Structure

```
stock_trader/
├── main.py                    # Entry point — menu, main loop
├── models/
│   ├── __init__.py
│   ├── stock.py               # Stock dataclass
│   ├── trade_order.py         # TradeOrder dataclass
│   ├── transaction.py         # Transaction record (Creator pattern)
│   ├── portfolio.py           # Portfolio — holds positions, cash (Expert pattern)
│   └── account.py             # Account — verifies funds (Expert pattern)
├── patterns/
│   ├── __init__.py
│   ├── order_builder.py       # OrderBuilder interface + MarketOrderBuilder (Builder pattern)
│   ├── trade_controller.py    # TradeController (Controller pattern)
│   └── trade_processor.py     # TradeProcessor — executes trades, creates transactions (Creator pattern)
├── services/
│   ├── __init__.py
│   ├── market_simulator.py    # Price simulator — random -5% to +5% every 10s
│   ├── research_service.py    # AI research (generates ratings, picks stock)
│   └── display_service.py     # Rich terminal UI — tables, panels, live display
├── graphs/
│   ├── __init__.py
│   ├── graph_builder.py       # Builder pattern for constructing LangGraph state graphs
│   ├── conventional_graph.py  # LangGraph StateGraph for conventional process
│   └── incremental_graph.py   # LangGraph StateGraph for iterative incremental process
└── config.py                  # Constants (initial prices, funds, limits)
```

---

## config.py — Constants

```python
INITIAL_FUNDS = 100_000.00
BUY_LIMIT = 5_000.00
MAX_HOLDING_PCT = 0.10          # 10% of total portfolio market value
PRICE_UPDATE_INTERVAL = 10      # seconds
PRICE_FLUCTUATION_RANGE = (-5, 5)  # -5% to +5%

INITIAL_WATCHLIST = {
    "AAPL": 264.80,
    "AMGN": 382.66,
    "XOM":  154.37,
    "GS":   861.89,
    "NVDA": 182.36,
    "ISRG": 496.17,
    "MSFT": 398.30,
    "MRK":  121.17,
    "CCL":   29.30,
    "NFLX":  97.72,
}
```

---

## Models (from Design Class Diagram)

### stock.py
```python
@dataclass
class Stock:
    ticker: str
    company_name: str
    price: float
    previous_price: float = 0.0

    @property
    def change_pct(self) -> float:
        if self.previous_price == 0:
            return 0.0
        return ((self.price - self.previous_price) / self.previous_price) * 100
```

### trade_order.py
```python
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
```

### transaction.py (Created by TradeProcessor — Creator pattern)
```python
@dataclass
class Transaction:
    id: str              # UUID
    trade_order: TradeOrder
    timestamp: datetime
    status: str          # "FILLED", "REJECTED"
```

### account.py (Expert pattern — owns balance data)
```python
class Account:
    balance: float

    def is_funds_sufficient(self, amount: float) -> bool:
        """Expert pattern: Account is the expert on fund sufficiency
        because it owns the balance data."""
        return self.balance >= amount

    def debit(self, amount: float) -> None: ...
    def credit(self, amount: float) -> None: ...
```

### portfolio.py
```python
class Portfolio:
    holdings: dict[str, PortfolioPosition]  # ticker -> {shares, avg_cost}
    account: Account

    def update_holdings(self, transaction: Transaction) -> None: ...
    def get_total_market_value(self, current_prices: dict) -> float: ...
    def is_within_holding_limit(self, ticker: str, additional_value: float, current_prices: dict) -> bool:
        """Check 10% max holding constraint."""
        ...
    def get_position(self, ticker: str) -> PortfolioPosition | None: ...
```

---

## Design Patterns (from answers.docx diagrams)

### 1. Controller Pattern — TradeController
```
TradeController is the first point of contact for system operations.
- Receives requests from the UI (terminal)
- Delegates to OrderBuilder and TradeProcessor
- Does NOT do business logic itself

Attributes:
  - trade_processor: TradeProcessor
  - order_builder: OrderBuilder

Methods:
  - handle_confirm_trade(data) -> confirmation
  - submit_trade_order(order_data: dict) -> TransactionReceipt
```

### 2. Expert Pattern — Account
```
Account is the Expert because it owns the balance data.
TradeProcessor asks Account: isFundsSufficient(totalCost) -> boolean
Account checks its own balance — no one else should.
```

### 3. Creator Pattern — TradeProcessor creates Transaction
```
TradeProcessor creates TransactionRecord because it records/uses the trade data.
TradeProcessor.createTransaction(orderData) -> Transaction
  - Transaction has: id (String), timestamp (DateTime)
```

### 4. Builder Pattern — OrderBuilder
```
Interface: OrderBuilder
  - set_stock(ticker)
  - set_qty(quantity)
  - set_order_type(type)
  - get_result() -> TradeOrder

Concrete: MarketOrderBuilder implements OrderBuilder
  - builds -> TradeOrder

Director: TradeController
  - Uses OrderBuilder to construct TradeOrder step by step
  - Calls: setTicker(data.ticker) -> setQty(data.qty) -> build() -> tradeOrder:TradeOrder
```

---

## Design Sequence (from answers.docx Design Sequence Diagram)

The flow for a trade execution:

```
1. User -> gui:TradeGUI          : clickConfirm()
2. gui:TradeGUI -> ctrl:TradeController : handleConfirmTrade(data)
3. ctrl:TradeController -> builder:OrderBuilder : setTicker(data.ticker)
4. ctrl:TradeController -> builder:OrderBuilder : setQty(data.qty)
5. ctrl:TradeController -> builder:OrderBuilder : build()
6. builder:OrderBuilder -> ctrl:TradeController : tradeOrder:TradeOrder
7. ctrl:TradeController -> proc:TradeProcessor  : process(tradeOrder)
8. proc:TradeProcessor -> acc:Account           : verifyFunds(tradeOrder.total)
9. acc:Account -> proc:TradeProcessor           : status:boolean
10. proc:TradeProcessor -> proc:TradeProcessor  : executeExchange(tradeOrder)  [simulated]
11. proc:TradeProcessor -> trans:Transaction     : <<create>>(tradeOrder)
12. proc:TradeProcessor -> port:Portfolio        : updateHoldings(trans)
13. proc:TradeProcessor -> ctrl:TradeController  : confirmation
14. ctrl:TradeController -> gui:TradeGUI         : receipt
15. gui:TradeGUI -> User                         : displayReceipt(receipt)
```

---

## LangGraph State Graphs

### Shared State (TypedDict)

```python
from typing import TypedDict, Optional

class TradingState(TypedDict):
    watchlist: dict[str, Stock]
    portfolio: Portfolio
    ratings: dict[str, str]          # ticker -> "BUY"/"SELL"/"HOLD"
    picked_stock: Optional[str]      # ticker or None
    picked_action: Optional[str]     # "BUY" or "SELL" or None
    trade_result: Optional[Transaction]
    message: str                     # status message for display
    mode: str                        # "ai" or "manual"
```

### Graph 1: Conventional Process

```
START -> research_node -> should_trade (conditional edge)
  -> YES -> trade_node -> update_portfolio_node -> END
  -> NO  -> END

Nodes:
- research_node: Evaluate all stocks, generate ratings, pick ONE stock (or none)
    - AI mode: auto-generate ratings based on price movement
    - Manual mode: display stocks, prompt user to pick
- trade_node: Execute buy ($5,000) or sell (all shares)
    - Uses TradeController -> OrderBuilder -> TradeProcessor flow
- update_portfolio_node: Update portfolio and balance

Conditional edge:
- should_trade: if picked_stock is None -> END, else -> trade_node
```

### Graph 2: Iterative Incremental Process

```
START -> research_node -> should_trade (conditional edge)
  -> YES -> incremental_trade_node -> assess_node -> should_continue (conditional edge)
      -> YES -> incremental_trade_node  (loop back)
      -> NO  -> END
  -> NO  -> END

Nodes:
- research_node: Same as conventional
- incremental_trade_node: Buy/sell only 1/3 of shares
- assess_node: Check if price moved favorably
    - BUY: if price went up within 1% -> continue buying
    - SELL: if price went down -> continue selling
    - Otherwise -> stop

Conditional edge:
- should_continue: check assessment result + remaining shares
```

### graph_builder.py (Builder pattern for graphs)

```python
"""
Builder pattern applied to constructing LangGraph StateGraphs.
This satisfies the assignment requirement:
'Teams are required to apply the builder pattern to design and implement these.'
"""

class TradingGraphBuilder:
    """Abstract builder interface for trading state graphs."""
    def set_research_node(self, node_fn): ...
    def set_trade_node(self, node_fn): ...
    def set_conditional_edges(self): ...
    def build(self) -> StateGraph: ...

class ConventionalGraphBuilder(TradingGraphBuilder):
    """Builds the conventional (one-shot) trading graph."""
    ...

class IncrementalGraphBuilder(TradingGraphBuilder):
    """Builds the iterative incremental trading graph with loop."""
    def set_assess_node(self, node_fn): ...
    ...

class GraphDirector:
    """Director that uses a builder to construct the graph."""
    def __init__(self, builder: TradingGraphBuilder): ...
    def construct(self, mode: str) -> CompiledGraph: ...
```

---

## Market Simulator

```python
class MarketSimulator:
    """Simulates stock price movement.
    For each stock: generate random float between -5 and +5,
    representing -5% to +5% fluctuation, update the price."""

    def update_prices(self, watchlist: dict[str, Stock]) -> None:
        for ticker, stock in watchlist.items():
            pct_change = random.uniform(-5, 5)
            stock.previous_price = stock.price
            stock.price = stock.price * (1 + pct_change / 100)
```

---

## Research Service

```python
class ResearchService:
    """AI-automated research: evaluates stocks and picks one."""

    def evaluate(self, watchlist, portfolio) -> tuple[dict, str | None, str | None]:
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
```

---

## Display Service (Rich Terminal)

```python
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout

class DisplayService:
    """Colorful terminal UI using rich library."""

    def show_menu(self) -> int: ...
    def show_watchlist(self, watchlist: dict[str, Stock]) -> Table:
        """Green ▲ for up, Red ▼ for down, yellow ★ for picked stock."""
    def show_portfolio(self, portfolio: Portfolio, prices: dict) -> Table: ...
    def show_research(self, ratings: dict, picked: str, action: str) -> Panel: ...
    def show_trade(self, transaction: Transaction) -> Panel: ...
    def show_state_flow(self, current_node: str) -> str:
        """Shows: START → Research → Pick? → Trade → Update → END
        with current node highlighted."""
    def show_incremental_step(self, step: int, shares: int, assessment: str) -> Panel: ...
```

**Color scheme:**
- Green (`[green]`): price up, BUY, successful trade, positive gain
- Red (`[red]`): price down, SELL, negative gain
- Yellow (`[yellow]`): highlights, picked stock, cash values, prompts
- Blue (`[blue]`): section headers
- Purple (`[purple]`): LangGraph state flow
- Dim/gray (`[dim]`): secondary info

---

## Main Loop (main.py)

```python
async def main():
    # Initialize
    portfolio = Portfolio(account=Account(balance=INITIAL_FUNDS))
    watchlist = {t: Stock(t, t, p) for t, p in INITIAL_WATCHLIST.items()}
    market = MarketSimulator()
    display = DisplayService()

    # Show menu
    choice = display.show_menu()
    # 1=Conventional AI, 2=Incremental AI, 3=Conventional Manual, 4=Incremental Manual

    # Build the appropriate graph using Builder pattern
    if choice in (1, 3):
        builder = ConventionalGraphBuilder()
    else:
        builder = IncrementalGraphBuilder()

    director = GraphDirector(builder)
    mode = "ai" if choice in (1, 2) else "manual"
    graph = director.construct(mode=mode)

    # Main loop with Rich Live display
    with Live(refresh_per_second=1) as live:
        while True:
            # Update prices every 10 seconds
            market.update_prices(watchlist)

            # Build initial state
            state = TradingState(
                watchlist=watchlist,
                portfolio=portfolio,
                ratings={},
                picked_stock=None,
                picked_action=None,
                trade_result=None,
                message="",
                mode=mode,
            )

            # Run the LangGraph
            result = graph.invoke(state)

            # Display everything
            layout = build_display(display, watchlist, portfolio, result)
            live.update(layout)

            # Wait 10 seconds
            time.sleep(PRICE_UPDATE_INTERVAL)
```

---

## Dependencies

```
pip install langgraph rich
```

No other external dependencies needed. No API keys needed (research is simulated, not real AI calls).

---

## Key Implementation Rules

1. **Every trade goes through the design sequence**: GUI -> TradeController -> OrderBuilder -> TradeProcessor -> Account -> Portfolio. Do NOT shortcut this.

2. **Builder pattern is used TWICE**: once for OrderBuilder (building TradeOrders) and once for GraphBuilder (building LangGraph StateGraphs).

3. **Expert pattern**: Only `Account` checks fund sufficiency. `TradeProcessor` must ask `Account`, never check the balance directly.

4. **Creator pattern**: Only `TradeProcessor` creates `Transaction` objects.

5. **Controller pattern**: `TradeController` is the single entry point. It delegates everything — no business logic in the controller.

6. **10% constraint**: Before any BUY, check that the stock's total holding won't exceed 10% of (portfolio market value + cash).

7. **Conventional SELL**: sells ALL shares of the picked stock.

8. **Incremental BUY**: buy 1/3 of shares at a time. If price goes up within 1%, buy more. Stop if direction changes or shares exhausted.

9. **Incremental SELL**: sell 1/3 of shares at a time. If price goes down (within 1%), sell more. Stop if price goes down too much or goes up.

10. **Price simulation**: `random.uniform(-5, 5)` percent change per stock per 10-second tick.

11. **Manual mode**: Instead of AI generating ratings, prompt the user via terminal input to select a stock and action.

---

## What This Maps To in the Answers Doc

| Work Item | Answers Doc Content | Implementation |
|-----------|-------------------|----------------|
| 1. Business Process | "Trade Stocks" process description | The main loop + LangGraph flow |
| 2. Domain Model | User, Account, Portfolio, Stock, TradeOrder classes | `models/` directory |
| 3. High-Level UC | TUCBW: select "New Trade", TUCEW: view confirmation | Menu selection → trade confirmation display |
| 4. Expanded UC | 8-step actor/system table | The full flow from user input to receipt |
| 5. GoF Patterns | Controller, Expert, Creator, Builder diagrams | `patterns/` directory |
| 6. Scenario Descriptions | Steps 5-7.6 | The TradeController → OrderBuilder → TradeProcessor → Account → Portfolio chain |
| 7. Scenario Tables | The step/subject/action/object table | Implemented as the method call chain |
| 8. Informal Seq Diagram | English-labeled sequence diagram | The node functions in LangGraph |
| 9. Design Seq Diagram | Typed method calls diagram | Exact method signatures in classes |
| 10. Design Class Diagram | TradeController, OrderBuilder, TradeProcessor, Account, Portfolio, Transaction | All classes with exact method signatures from the diagram |
| 11. Implementation | **Required** — code + demo | This entire codebase |
