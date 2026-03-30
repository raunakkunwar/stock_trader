# UC3 Stock Trading Simulator

A Python terminal application that simulates stock trading using **LangGraph** for state machine graphs and **Rich** for colorful terminal UI. Built as part of Team Assignment UC3, implementing four GoF design patterns and two trading processes.

---

## What This Does

This app simulates stock trading with a portfolio of 10 real stocks. Every 10 seconds, stock prices fluctuate randomly (between -5% and +5%), and the system either automatically or manually researches, rates, and trades stocks.

**Two Trading Processes:**

| Process | How It Works |
|---------|-------------|
| **Conventional** | Research all stocks, pick one, buy $5,000 worth or sell ALL shares in one shot |
| **Iterative Incremental** | Same research, but buys/sells in **1/3 increments**, assessing after each step. Continues if price moves favorably (within 1%), stops if direction changes |

**Two Modes:**

| Mode | How It Works |
|------|-------------|
| **AI Automated** | The system automatically rates stocks and picks the best trade every 10 seconds |
| **Manual** | You see the ratings and choose which stock to buy/sell each round |

---

## Design Patterns Implemented

| Pattern | Class | Purpose |
|---------|-------|---------|
| **Controller** | `TradeController` | Single entry point for trade requests. Delegates to builder and processor, contains no business logic |
| **Builder** (x2) | `MarketOrderBuilder` | Constructs `TradeOrder` objects step by step |
| | `ConventionalGraphBuilder` / `IncrementalGraphBuilder` | Constructs LangGraph `StateGraph` objects for each trading process |
| **Creator** | `TradeProcessor` | Creates `Transaction` records because it records and uses trade data |
| **Expert** | `Account` | Only class that checks fund sufficiency, because it owns the balance data |

---

## LangGraph State Machines

### Conventional Process
```
START -> Research -> Stocks Picked? -> YES -> Trade -> Update Portfolio -> END
                                    -> NO  -> END
```

### Iterative Incremental Process
```
START -> Research -> Stocks Picked? -> YES -> Trade (1/3) -> Assess -> Continue? -> YES -> Trade (loop)
                                    -> NO  -> END                                -> NO  -> END
```

---

## Trade Execution Flow (Design Sequence)

Every trade follows this exact chain:

```
User -> TradeController -> OrderBuilder (build TradeOrder step by step)
     -> TradeProcessor  -> Account (verify funds - Expert pattern)
                        -> Execute trade
                        -> Create Transaction (Creator pattern)
                        -> Update Portfolio
     -> Display receipt to user
```

---

## Project Structure

```
stock_trader/
├── main.py                      # Entry point - menu, main loop
├── config.py                    # Constants (initial prices, funds, limits)
├── test_all.py                  # Comprehensive test suite (131 tests)
├── ARCHITECTURE.md              # Full architecture & implementation guide
├── models/
│   ├── stock.py                 # Stock dataclass with price tracking
│   ├── trade_order.py           # TradeOrder dataclass
│   ├── transaction.py           # Transaction record (Creator pattern)
│   ├── account.py               # Account - fund verification (Expert pattern)
│   └── portfolio.py             # Portfolio - holdings management
├── patterns/
│   ├── order_builder.py         # OrderBuilder interface + MarketOrderBuilder (Builder)
│   ├── trade_controller.py      # TradeController (Controller pattern)
│   └── trade_processor.py       # TradeProcessor (Creator + Expert patterns)
├── services/
│   ├── market_simulator.py      # Random price fluctuation simulator
│   ├── research_service.py      # AI stock evaluation and picking
│   └── display_service.py       # Rich terminal UI (tables, panels, colors)
└── graphs/
    ├── graph_builder.py         # Builder pattern for LangGraph StateGraphs
    ├── conventional_graph.py    # Conventional process nodes and edges
    └── incremental_graph.py     # Incremental process nodes and edges
```

---

## How to Run

### Prerequisites

- Python 3.10 or higher

### Install Dependencies

```bash
pip install -r requirements.txt
```

No API keys needed. The AI research is simulated locally using price movement logic. LangGraph is used purely as a state machine framework.

### Run the App

```bash
python main.py
```

You will see a menu:

```
1. Conventional Process - AI Automated
2. Iterative Incremental Process - AI Automated
3. Conventional Process - Manual
4. Iterative Incremental Process - Manual
5. Exit
```

- **Options 1 & 2 (AI):** Runs automatically. Prices update every 10 seconds, trades execute automatically. Watch it go. Press `Ctrl+C` to stop.
- **Options 3 & 4 (Manual):** Each round shows you updated prices and ratings. You pick the stock and action (BUY/SELL). Press Enter for next round, or type `q` to quit.

### Run Tests

```bash
python test_all.py
```

Runs 131 tests covering all models, patterns, services, graphs, edge cases, and full simulations.

---

## Trading Rules

| Rule | Detail |
|------|--------|
| Initial funds | $100,000 |
| Buy amount | $5,000 per trade |
| Max holding | No stock can exceed 10% of total portfolio market value |
| Conventional sell | Sells ALL shares of the picked stock |
| Incremental buy | Buys 1/3 of shares at a time. Continues if price goes up within 1% |
| Incremental sell | Sells 1/3 of shares at a time. Continues if price goes down within 1% |
| Price updates | Every 10 seconds, each stock moves randomly between -5% and +5% |
| AI ratings | Price up > 2% = BUY, down > 2% = SELL, otherwise HOLD |

---

## Watchlist (Initial Prices)

| Ticker | Price |
|--------|-------|
| AAPL | $264.80 |
| AMGN | $382.66 |
| XOM | $154.37 |
| GS | $861.89 |
| NVDA | $182.36 |
| ISRG | $496.17 |
| MSFT | $398.30 |
| MRK | $121.17 |
| CCL | $29.30 |
| NFLX | $97.72 |

---

## Technologies

- **Python 3.10+**
- **LangGraph** - State machine framework for defining trading process graphs
- **Rich** - Terminal UI library for colorful tables, panels, and live displays
