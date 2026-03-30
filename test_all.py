"""UC3 Stock Trading Simulator — Comprehensive Test Suite"""
import math
import sys

passed = 0
failed = 0

def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS: {name}")
    else:
        failed += 1
        print(f"  FAIL: {name} -- {detail}")


print("=" * 60)
print("  UC3 STOCK TRADING SIMULATOR — FULL TEST SUITE")
print("=" * 60)

# ============================================================
print("\n--- 1. CONFIG VALUES ---")
from config import (
    INITIAL_FUNDS, BUY_LIMIT, MAX_HOLDING_PCT,
    PRICE_UPDATE_INTERVAL, PRICE_FLUCTUATION_RANGE, INITIAL_WATCHLIST,
)

test("Initial funds = 100000", INITIAL_FUNDS == 100_000.00)
test("Buy limit = 5000", BUY_LIMIT == 5_000.00)
test("Max holding = 10%", MAX_HOLDING_PCT == 0.10)
test("Price update interval = 10s", PRICE_UPDATE_INTERVAL == 10)
test("Fluctuation range = (-5, 5)", PRICE_FLUCTUATION_RANGE == (-5, 5))
test("Watchlist has 10 stocks", len(INITIAL_WATCHLIST) == 10)
test("AAPL = 264.80", INITIAL_WATCHLIST["AAPL"] == 264.80)
test("GS = 861.89", INITIAL_WATCHLIST["GS"] == 861.89)
test("CCL = 29.30", INITIAL_WATCHLIST["CCL"] == 29.30)
test("NFLX = 97.72", INITIAL_WATCHLIST["NFLX"] == 97.72)

# ============================================================
print("\n--- 2. STOCK MODEL ---")
from models import Stock

s = Stock("AAPL", "Apple", 105.0, 100.0)
test("Stock price up 5%", abs(s.change_pct - 5.0) < 0.01)
s2 = Stock("X", "X", 95.0, 100.0)
test("Stock price down 5%", abs(s2.change_pct - (-5.0)) < 0.01)
s3 = Stock("X", "X", 100.0, 100.0)
test("Stock no change = 0%", s3.change_pct == 0.0)
s4 = Stock("X", "X", 50.0)
test("Stock no previous = 0%", s4.change_pct == 0.0)
s5 = Stock("X", "X", 0.01, 100.0)
test("Stock massive drop", s5.change_pct < -99.0)

# ============================================================
print("\n--- 3. TRADE ORDER MODEL ---")
from models import TradeOrder

o = TradeOrder("AAPL", 10, "BUY", 150.0)
test("Order total = qty * price", o.total == 1500.0)
o2 = TradeOrder("X", 0, "BUY", 100.0)
test("Zero qty order total = 0", o2.total == 0.0)
o3 = TradeOrder("X", 1, "BUY", 0.01)
test("Penny stock order", o3.total == 0.01)

# ============================================================
print("\n--- 4. TRANSACTION (CREATOR PATTERN) ---")
from models import Transaction

tx1 = Transaction.create(o, "FILLED")
tx2 = Transaction.create(o, "REJECTED")
test("Transaction has unique ID", tx1.id != tx2.id)
test("Transaction ID length = 8", len(tx1.id) == 8)
test("Filled status", tx1.status == "FILLED")
test("Rejected status", tx2.status == "REJECTED")
test("Transaction has timestamp", tx1.timestamp is not None)
test("Transaction links to order", tx1.trade_order == o)

# ============================================================
print("\n--- 5. ACCOUNT (EXPERT PATTERN) ---")
from models import Account

a = Account(balance=100_000.0)
test("Initial balance 100k", a.balance == 100_000.0)
test("Funds sufficient for 50k", a.is_funds_sufficient(50_000.0))
test("Funds sufficient for exact amount", a.is_funds_sufficient(100_000.0))
test("Funds NOT sufficient for 100001", not a.is_funds_sufficient(100_001.0))
test("Funds sufficient for 0", a.is_funds_sufficient(0.0))

a.debit(30_000.0)
test("Debit 30k -> balance 70k", a.balance == 70_000.0)
a.credit(10_000.0)
test("Credit 10k -> balance 80k", a.balance == 80_000.0)

try:
    a.debit(999_999.0)
    test("Debit exceeding balance raises error", False, "No error raised")
except ValueError:
    test("Debit exceeding balance raises error", True)

a2 = Account(balance=0.0)
test("Zero balance insufficient for any amount", not a2.is_funds_sufficient(0.01))
test("Zero balance sufficient for 0", a2.is_funds_sufficient(0.0))

# ============================================================
print("\n--- 6. PORTFOLIO ---")
from models import Portfolio, PortfolioPosition

acc = Account(balance=100_000.0)
port = Portfolio(account=acc)
test("Empty portfolio", len(port.holdings) == 0)
test("Total value = cash when empty", port.get_total_market_value({}) == 100_000.0)

# BUY 10 AAPL @ 150
buy1 = Transaction.create(TradeOrder("AAPL", 10, "BUY", 150.0), "FILLED")
port.update_holdings(buy1)
test("BUY adds holding", "AAPL" in port.holdings)
test("BUY correct shares", port.holdings["AAPL"].shares == 10)
test("BUY correct avg cost", port.holdings["AAPL"].avg_cost == 150.0)

# BUY 10 more AAPL @ 200 (avg cost should update)
buy2 = Transaction.create(TradeOrder("AAPL", 10, "BUY", 200.0), "FILLED")
port.update_holdings(buy2)
test("Second BUY updates shares to 20", port.holdings["AAPL"].shares == 20)
expected_avg = (10 * 150 + 10 * 200) / 20  # 175
test("Avg cost updated correctly", abs(port.holdings["AAPL"].avg_cost - 175.0) < 0.01)

# REJECTED transaction should NOT update
rej = Transaction.create(TradeOrder("AAPL", 100, "BUY", 999.0), "REJECTED")
port.update_holdings(rej)
test("Rejected TX does not change holdings", port.holdings["AAPL"].shares == 20)

# SELL partial
sell1 = Transaction.create(TradeOrder("AAPL", 5, "SELL", 180.0), "FILLED")
port.update_holdings(sell1)
test("Partial sell reduces shares", port.holdings["AAPL"].shares == 15)

# SELL all remaining
sell_all = Transaction.create(TradeOrder("AAPL", 15, "SELL", 190.0), "FILLED")
port.update_holdings(sell_all)
test("Sell all removes from holdings", "AAPL" not in port.holdings)

# Total market value with holdings
acc3 = Account(balance=50_000.0)
port3 = Portfolio(account=acc3)
port3.holdings["MSFT"] = PortfolioPosition(shares=100, avg_cost=300.0)
mv = port3.get_total_market_value({"MSFT": 400.0})
test("Market value = cash + holdings", mv == 50_000.0 + 100 * 400.0)

# 10% holding limit
test("Within 10% limit", port3.is_within_holding_limit("NEW", 5_000.0, {"MSFT": 400.0}))
test("Exceeds 10% limit", not port3.is_within_holding_limit("NEW", 100_000.0, {"MSFT": 400.0}))
# MSFT is 100*400=40k out of 90k total (44%), so adding more is correctly blocked
test("Existing stock over limit blocked", not port3.is_within_holding_limit("MSFT", 1_000.0, {"MSFT": 400.0}))
# Test a small holding that IS within limit
acc_small = Account(balance=100_000.0)
port_small = Portfolio(account=acc_small)
port_small.holdings["AAPL"] = PortfolioPosition(shares=2, avg_cost=250.0)
# AAPL = 2*265 = 530 out of 100530 total. 10% = 10053. 530+1000=1530 < 10053
test("Small holding within limit OK", port_small.is_within_holding_limit("AAPL", 1_000.0, {"AAPL": 265.0}))

# ============================================================
print("\n--- 7. ORDER BUILDER (BUILDER PATTERN) ---")
from patterns import MarketOrderBuilder

b = MarketOrderBuilder()
order = b.set_stock("NVDA", 182.36).set_quantity(27).set_side("BUY").set_order_type("MARKET").build()
test("Builder sets ticker", order.ticker == "NVDA")
test("Builder sets quantity", order.quantity == 27)
test("Builder sets side", order.side == "BUY")
test("Builder sets price", order.price_at_order == 182.36)
test("Builder sets order type", order.order_type == "MARKET")
test("Builder total correct", abs(order.total - 27 * 182.36) < 0.01)

try:
    MarketOrderBuilder().set_quantity(5).build()
    test("Builder incomplete order raises error", False)
except ValueError:
    test("Builder incomplete order raises error", True)

try:
    MarketOrderBuilder().set_stock("X", 10.0).set_quantity(0).build()
    test("Builder zero qty raises error", False)
except ValueError:
    test("Builder zero qty raises error", True)

# ============================================================
print("\n--- 8. TRADE PROCESSOR (CREATOR + EXPERT) ---")
from patterns import TradeProcessor

# Successful BUY
a8 = Account(balance=100_000.0)
p8 = Portfolio(account=a8)
proc = TradeProcessor(a8, p8)
prices = {"AAPL": 265.0}
buy_o = TradeOrder("AAPL", 18, "BUY", 265.0)
tx = proc.process(buy_o, prices)
test("BUY filled", tx.status == "FILLED")
test("Balance debited", a8.balance == 100_000.0 - 18 * 265.0)
test("Holdings updated", p8.holdings["AAPL"].shares == 18)

# BUY rejected: insufficient funds
a9 = Account(balance=100.0)
p9 = Portfolio(account=a9)
proc9 = TradeProcessor(a9, p9)
tx9 = proc9.process(TradeOrder("GS", 10, "BUY", 860.0), {"GS": 860.0})
test("BUY rejected: insufficient funds", tx9.status == "REJECTED")
test("Balance unchanged on rejection", a9.balance == 100.0)

# BUY rejected: exceeds 10% holding
a10 = Account(balance=100_000.0)
p10 = Portfolio(account=a10)
proc10 = TradeProcessor(a10, p10)
tx10 = proc10.process(TradeOrder("GS", 60, "BUY", 860.0), {"GS": 860.0})
test("BUY rejected: exceeds 10% limit", tx10.status == "REJECTED")

# SELL successful
a11 = Account(balance=50_000.0)
p11 = Portfolio(account=a11)
p11.holdings["AAPL"] = PortfolioPosition(shares=20, avg_cost=250.0)
proc11 = TradeProcessor(a11, p11)
tx11 = proc11.process(TradeOrder("AAPL", 20, "SELL", 270.0), {"AAPL": 270.0})
test("SELL filled", tx11.status == "FILLED")
test("SELL credited balance", a11.balance == 50_000.0 + 20 * 270.0)
test("SELL removed holdings", "AAPL" not in p11.holdings)

# SELL rejected: dont own stock
a12 = Account(balance=50_000.0)
p12 = Portfolio(account=a12)
proc12 = TradeProcessor(a12, p12)
tx12 = proc12.process(TradeOrder("MSFT", 10, "SELL", 400.0), {"MSFT": 400.0})
test("SELL rejected: no position", tx12.status == "REJECTED")

# SELL rejected: not enough shares
a13 = Account(balance=50_000.0)
p13 = Portfolio(account=a13)
p13.holdings["NVDA"] = PortfolioPosition(shares=5, avg_cost=180.0)
proc13 = TradeProcessor(a13, p13)
tx13 = proc13.process(TradeOrder("NVDA", 10, "SELL", 190.0), {"NVDA": 190.0})
test("SELL rejected: insufficient shares", tx13.status == "REJECTED")

# ============================================================
print("\n--- 9. TRADE CONTROLLER (CONTROLLER PATTERN) ---")
from patterns import TradeController

a14 = Account(balance=100_000.0)
p14 = Portfolio(account=a14)
proc14 = TradeProcessor(a14, p14)
ctrl = TradeController(proc14)

tx14 = ctrl.submit_trade_order("AAPL", 265.0, 18, "BUY", {"AAPL": 265.0})
test("Controller BUY full chain", tx14.status == "FILLED")
test("Controller updates portfolio", "AAPL" in p14.holdings)

tx15 = ctrl.submit_trade_order("AAPL", 270.0, 18, "SELL", {"AAPL": 270.0})
test("Controller SELL works", tx15.status == "FILLED")
test("Controller SELL empties position", "AAPL" not in p14.holdings)

tx16 = ctrl.submit_trade_order("GS", 860.0, 999, "BUY", {"GS": 860.0})
test("Controller handles rejection", tx16.status == "REJECTED")

# ============================================================
print("\n--- 10. MARKET SIMULATOR ---")
from services import MarketSimulator

market = MarketSimulator()
wl = {t: Stock(t, t, p) for t, p in INITIAL_WATCHLIST.items()}

all_in_bounds = True
for _ in range(100):
    old = {t: s.price for t, s in wl.items()}
    market.update_prices(wl)
    for t, s in wl.items():
        change = abs(s.change_pct)
        if change > 5.5:
            all_in_bounds = False

test("Price changes within bounds (100 rounds)", all_in_bounds)
test("Previous prices tracked", all(s.previous_price > 0 for s in wl.values()))
test("Prices are positive", all(s.price > 0 for s in wl.values()))

# ============================================================
print("\n--- 11. RESEARCH SERVICE ---")
from services import ResearchService

research = ResearchService()

# Case 1: Strong BUY candidate
twl1 = {
    "UP": Stock("UP", "Up", 105.0, 100.0),
    "DOWN": Stock("DOWN", "Dn", 95.0, 100.0),
    "FLAT": Stock("FLAT", "Fl", 100.5, 100.0),
}
ra = Account(balance=100_000.0)
rp = Portfolio(account=ra)
ratings, picked, action = research.evaluate(twl1, rp, {t: s.price for t, s in twl1.items()})
test("Ratings: UP=BUY", ratings["UP"] == "BUY")
test("Ratings: DOWN=SELL", ratings["DOWN"] == "SELL")
test("Ratings: FLAT=HOLD", ratings["FLAT"] == "HOLD")
test("Picks strongest mover", picked is not None)

# Case 2: No funds -> skip BUY
ra2 = Account(balance=0.0)
rp2 = Portfolio(account=ra2)
twl2 = {"UP": Stock("UP", "Up", 105.0, 100.0)}
ratings2, picked2, action2 = research.evaluate(twl2, rp2, {"UP": 105.0})
test("No funds -> cannot BUY", picked2 is None)

# Case 3: All HOLD
twl3 = {
    "A": Stock("A", "A", 100.5, 100.0),
    "B": Stock("B", "B", 99.5, 100.0),
}
ra3 = Account(balance=100_000.0)
rp3 = Portfolio(account=ra3)
ratings3, picked3, action3 = research.evaluate(twl3, rp3, {t: s.price for t, s in twl3.items()})
test("All HOLD -> no pick", picked3 is None)

# Case 4: SELL only if you own it
twl4 = {"DOWN": Stock("DOWN", "Dn", 95.0, 100.0)}
ra4 = Account(balance=100_000.0)
rp4 = Portfolio(account=ra4)
ratings4, picked4, action4 = research.evaluate(twl4, rp4, {"DOWN": 95.0})
test("SELL candidate but no position -> no pick", picked4 is None)

# Case 5: SELL when you own it
rp4.holdings["DOWN"] = PortfolioPosition(shares=10, avg_cost=100.0)
ratings5, picked5, action5 = research.evaluate(twl4, rp4, {"DOWN": 95.0})
test("SELL with position -> picks SELL", picked5 == "DOWN" and action5 == "SELL")

# ============================================================
print("\n--- 12. CONVENTIONAL LANGGRAPH ---")
from graphs.graph_builder import ConventionalGraphBuilder, IncrementalGraphBuilder
from graphs.conventional_graph import (
    TradingState, research_node, should_trade, trade_node, update_portfolio_node,
)
from services import DisplayService

display = DisplayService()

cb = ConventionalGraphBuilder(TradingState)
cb.set_research_node(research_node)
cb.set_trade_node(trade_node)
cb.set_update_node(update_portfolio_node)
cb.set_conditional_edges(should_trade_fn=should_trade)
conv_graph = cb.build()
test("Conventional graph compiles", conv_graph is not None)

# Case A: BUY on price up
ga = Account(balance=100_000.0)
gp = Portfolio(account=ga)
gwl = {"AAPL": Stock("AAPL", "Apple", 280.0, 260.0)}
state_a = {
    "watchlist": gwl, "portfolio": gp, "ratings": {},
    "picked_stock": None, "picked_action": None,
    "trade_result": None, "message": "", "mode": "ai", "display": display,
}
res_a = conv_graph.invoke(state_a)
test("Conv AI: picks BUY on price up", res_a["picked_action"] == "BUY")
test("Conv AI: trade filled", res_a["trade_result"].status == "FILLED")
test("Conv AI: portfolio updated", "AAPL" in gp.holdings)
test("Conv AI: balance debited", ga.balance < 100_000.0)
expected_shares = max(1, math.floor(5000 / 280.0))
test(f"Conv AI: bought ~$5000 worth ({expected_shares} shares)", gp.holdings["AAPL"].shares == expected_shares)

# Case B: SELL ALL on price down
gb = Account(balance=90_000.0)
gpb = Portfolio(account=gb)
gpb.holdings["MSFT"] = PortfolioPosition(shares=20, avg_cost=400.0)
gwl_b = {"MSFT": Stock("MSFT", "MS", 380.0, 400.0)}
state_b = {
    "watchlist": gwl_b, "portfolio": gpb, "ratings": {},
    "picked_stock": None, "picked_action": None,
    "trade_result": None, "message": "", "mode": "ai", "display": display,
}
res_b = conv_graph.invoke(state_b)
test("Conv SELL: picks SELL on price down", res_b["picked_action"] == "SELL")
test("Conv SELL: sells ALL shares", "MSFT" not in gpb.holdings)
test("Conv SELL: balance credited", gb.balance == 90_000.0 + 20 * 380.0)

# Case C: No actionable stock -> skip
gc = Account(balance=100_000.0)
gpc = Portfolio(account=gc)
gwl_c = {"FLAT": Stock("FLAT", "Fl", 100.5, 100.0)}
state_c = {
    "watchlist": gwl_c, "portfolio": gpc, "ratings": {},
    "picked_stock": None, "picked_action": None,
    "trade_result": None, "message": "", "mode": "ai", "display": display,
}
res_c = conv_graph.invoke(state_c)
test("Conv: no pick -> no trade", res_c["picked_stock"] is None)
test("Conv: balance unchanged", gc.balance == 100_000.0)

# ============================================================
print("\n--- 13. INCREMENTAL LANGGRAPH ---")
from graphs.incremental_graph import (
    IncrementalState, research_node as ir, should_trade as ist,
    incremental_trade_node, assess_node, should_continue,
)

ib = IncrementalGraphBuilder(IncrementalState)
ib.set_research_node(ir)
ib.set_trade_node(incremental_trade_node)
ib.set_assess_node(assess_node)
ib.set_conditional_edges(should_trade_fn=ist, should_continue_fn=should_continue)
inc_graph = ib.build()
test("Incremental graph compiles", inc_graph is not None)

# Case A: Incremental BUY
ia = Account(balance=100_000.0)
ip = Portfolio(account=ia)
iwl = {"NVDA": Stock("NVDA", "Nvidia", 195.0, 180.0)}
im = MarketSimulator()
state_i = {
    "watchlist": iwl, "portfolio": ip, "ratings": {},
    "picked_stock": None, "picked_action": None,
    "trade_result": None, "message": "", "mode": "ai", "display": display,
    "remaining_shares": 0, "total_shares": 0, "increment_step": 0,
    "continue_trading": False, "price_at_start": 0.0, "market_simulator": im,
}
res_i = inc_graph.invoke(state_i)
test("Incr BUY: picks NVDA", res_i["picked_stock"] == "NVDA")
test("Incr BUY: at least 1 step", res_i["increment_step"] >= 1)
test("Incr BUY: trade executed", res_i["trade_result"] is not None)

# Case B: Incremental SELL
ib_acc = Account(balance=50_000.0)
ib_port = Portfolio(account=ib_acc)
ib_port.holdings["XOM"] = PortfolioPosition(shares=30, avg_cost=150.0)
iwl_b = {"XOM": Stock("XOM", "Exxon", 140.0, 150.0)}
im2 = MarketSimulator()
state_ib = {
    "watchlist": iwl_b, "portfolio": ib_port, "ratings": {},
    "picked_stock": None, "picked_action": None,
    "trade_result": None, "message": "", "mode": "ai", "display": display,
    "remaining_shares": 0, "total_shares": 0, "increment_step": 0,
    "continue_trading": False, "price_at_start": 0.0, "market_simulator": im2,
}
res_ib = inc_graph.invoke(state_ib)
test("Incr SELL: picks SELL", res_ib["picked_action"] == "SELL")
test("Incr SELL: at least 1 step", res_ib["increment_step"] >= 1)

# Case C: No pick -> skip
ic_acc = Account(balance=100_000.0)
ic_port = Portfolio(account=ic_acc)
iwl_c = {"FLAT": Stock("FLAT", "Fl", 100.2, 100.0)}
im3 = MarketSimulator()
state_ic = {
    "watchlist": iwl_c, "portfolio": ic_port, "ratings": {},
    "picked_stock": None, "picked_action": None,
    "trade_result": None, "message": "", "mode": "ai", "display": display,
    "remaining_shares": 0, "total_shares": 0, "increment_step": 0,
    "continue_trading": False, "price_at_start": 0.0, "market_simulator": im3,
}
res_ic = inc_graph.invoke(state_ic)
test("Incr: no pick -> no trade", res_ic["picked_stock"] is None)

# ============================================================
print("\n--- 14. DISPLAY SERVICE ---")
d = DisplayService()
test("show_watchlist returns Table", d.show_watchlist({"A": Stock("A", "A", 100, 95)}) is not None)
test("show_watchlist with pick", d.show_watchlist({"A": Stock("A", "A", 100, 95)}, "A") is not None)
test("show_portfolio renders", d.show_portfolio(Portfolio(account=Account(1000)), {"A": 100}) is not None)
test("show_research renders", d.show_research({"A": "BUY"}, "A", "BUY") is not None)
test("show_research no pick", d.show_research({"A": "HOLD"}, None, None) is not None)
test("show_trade FILLED", d.show_trade(Transaction.create(TradeOrder("A", 10, "BUY", 100), "FILLED")) is not None)
test("show_trade REJECTED", d.show_trade(Transaction.create(TradeOrder("A", 10, "SELL", 100), "REJECTED")) is not None)
test("show_state_flow conventional", d.show_state_flow("Research", False) is not None)
test("show_state_flow incremental", d.show_state_flow("Assess", True) is not None)
test("show_incremental_step", d.show_incremental_step(1, 5, 15, "OK") is not None)

# ============================================================
print("\n--- 15. EDGE CASES ---")

# Edge: Buy with exact funds (but 10% rule must also pass)
ea = Account(balance=50_000.0)
ep = Portfolio(account=ea)
eproc = TradeProcessor(ea, ep)
ectrl = TradeController(eproc)
# 170 * 29.30 = 4981.00. 10% of 50k = 5k. 4981 < 5k -> OK
etx = ectrl.submit_trade_order("CCL", 29.30, 170, "BUY", {"CCL": 29.30})
test("Edge: buy within both fund and 10% limits", etx.status == "FILLED")
test("Edge: balance debited correctly", abs(ea.balance - (50_000.0 - 4981.0)) < 0.01)

# Edge: Sell stock with 1 share
ea2 = Account(balance=1000.0)
ep2 = Portfolio(account=ea2)
ep2.holdings["MRK"] = PortfolioPosition(shares=1, avg_cost=121.17)
eproc2 = TradeProcessor(ea2, ep2)
etx2 = eproc2.process(TradeOrder("MRK", 1, "SELL", 125.0), {"MRK": 125.0})
test("Edge: sell single share", etx2.status == "FILLED")
test("Edge: position removed after last share", "MRK" not in ep2.holdings)

# Edge: Multiple buys of same stock (10% limit caps accumulation)
ea3 = Account(balance=100_000.0)
ep3 = Portfolio(account=ea3)
eproc3 = TradeProcessor(ea3, ep3)
results3 = []
for i in range(5):
    tx3 = eproc3.process(TradeOrder("NFLX", 50, "BUY", 97.72), {"NFLX": 97.72})
    results3.append(tx3.status)
# First 2 buys fill (100 shares = $9,772 < 10% of ~$100k), then 10% blocks further
test("Edge: first buy fills", results3[0] == "FILLED")
test("Edge: 10% limit eventually blocks", "REJECTED" in results3)
test("Edge: holdings reflect filled buys only", ep3.holdings["NFLX"].shares == 100)

# Edge: 10% limit blocks large position
ea4 = Account(balance=100_000.0)
ep4 = Portfolio(account=ea4)
ep4.holdings["GS"] = PortfolioPosition(shares=11, avg_cost=860.0)
eproc4 = TradeProcessor(ea4, ep4)
etx4 = eproc4.process(TradeOrder("GS", 5, "BUY", 860.0), {"GS": 860.0})
test("Edge: 10% limit blocks over-concentration", etx4.status == "REJECTED")

# Edge: negative balance protection
ea5 = Account(balance=500.0)
ep5 = Portfolio(account=ea5)
eproc5 = TradeProcessor(ea5, ep5)
etx5 = eproc5.process(TradeOrder("MSFT", 10, "BUY", 400.0), {"MSFT": 400.0})
test("Edge: no negative balance", etx5.status == "REJECTED")
test("Edge: balance unchanged on reject", ea5.balance == 500.0)

# Edge: Buy then immediately sell
ea6 = Account(balance=100_000.0)
ep6 = Portfolio(account=ea6)
eproc6 = TradeProcessor(ea6, ep6)
eproc6.process(TradeOrder("AAPL", 10, "BUY", 265.0), {"AAPL": 265.0})
bal_after_buy = ea6.balance
etx6 = eproc6.process(TradeOrder("AAPL", 10, "SELL", 270.0), {"AAPL": 270.0})
test("Edge: buy then sell works", etx6.status == "FILLED")
test("Edge: profit reflected in balance", ea6.balance > bal_after_buy)
test("Edge: no holdings after full sell", "AAPL" not in ep6.holdings)

# ============================================================
print("\n--- 16. FULL SIMULATION (10 ROUNDS) ---")
sim_acc = Account(balance=100_000.0)
sim_port = Portfolio(account=sim_acc)
sim_wl = {t: Stock(t, t, p) for t, p in INITIAL_WATCHLIST.items()}
sim_market = MarketSimulator()
sim_display = DisplayService()

for rnd in range(10):
    sim_market.update_prices(sim_wl)
    prices = {t: s.price for t, s in sim_wl.items()}
    state = {
        "watchlist": sim_wl, "portfolio": sim_port, "ratings": {},
        "picked_stock": None, "picked_action": None,
        "trade_result": None, "message": "", "mode": "ai", "display": sim_display,
    }
    result = conv_graph.invoke(state)
    tv = sim_port.get_total_market_value(prices)

test("10-round sim: portfolio value positive", tv > 0)
test("10-round sim: balance non-negative", sim_acc.balance >= 0)
test("10-round sim: all holdings valid", all(p.shares > 0 for p in sim_port.holdings.values()))

# Incremental sim
sim2_acc = Account(balance=100_000.0)
sim2_port = Portfolio(account=sim2_acc)
sim2_wl = {t: Stock(t, t, p) for t, p in INITIAL_WATCHLIST.items()}
sim2_market = MarketSimulator()

for rnd in range(10):
    sim2_market.update_prices(sim2_wl)
    prices2 = {t: s.price for t, s in sim2_wl.items()}
    state2 = {
        "watchlist": sim2_wl, "portfolio": sim2_port, "ratings": {},
        "picked_stock": None, "picked_action": None,
        "trade_result": None, "message": "", "mode": "ai", "display": sim_display,
        "remaining_shares": 0, "total_shares": 0, "increment_step": 0,
        "continue_trading": False, "price_at_start": 0.0, "market_simulator": sim2_market,
    }
    result2 = inc_graph.invoke(state2)
    tv2 = sim2_port.get_total_market_value(prices2)

test("10-round incr sim: portfolio value positive", tv2 > 0)
test("10-round incr sim: balance non-negative", sim2_acc.balance >= 0)
test("10-round incr sim: all holdings valid", all(p.shares > 0 for p in sim2_port.holdings.values()))

# ============================================================
print()
print("=" * 60)
print(f"  RESULTS: {passed} PASSED, {failed} FAILED out of {passed + failed}")
print("=" * 60)
if failed > 0:
    sys.exit(1)
