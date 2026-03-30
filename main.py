import time
import sys
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.live import Live
from rich.layout import Layout
from rich.text import Text

from config import INITIAL_FUNDS, INITIAL_WATCHLIST, PRICE_UPDATE_INTERVAL
from models.stock import Stock
from models.portfolio import Portfolio
from models.account import Account
from services.market_simulator import MarketSimulator
from services.display_service import DisplayService
from graphs.graph_builder import ConventionalGraphBuilder, IncrementalGraphBuilder, GraphDirector
from graphs.conventional_graph import (
    TradingState,
    research_node as conv_research,
    should_trade as conv_should_trade,
    trade_node as conv_trade,
    update_portfolio_node as conv_update,
)
from graphs.incremental_graph import (
    IncrementalState,
    research_node as inc_research,
    should_trade as inc_should_trade,
    incremental_trade_node as inc_trade,
    assess_node as inc_assess,
    should_continue as inc_should_continue,
)

console = Console()


def build_conventional_graph():
    builder = ConventionalGraphBuilder(TradingState)
    builder.set_research_node(conv_research)
    builder.set_trade_node(conv_trade)
    builder.set_update_node(conv_update)
    builder.set_conditional_edges(should_trade_fn=conv_should_trade)
    return builder.build()


def build_incremental_graph():
    builder = IncrementalGraphBuilder(IncrementalState)
    builder.set_research_node(inc_research)
    builder.set_trade_node(inc_trade)
    builder.set_assess_node(inc_assess)
    builder.set_conditional_edges(
        should_trade_fn=inc_should_trade,
        should_continue_fn=inc_should_continue,
    )
    return builder.build()


def build_display_layout(display, watchlist, portfolio, result, is_incremental=False):
    """Build a rich layout showing all current state."""
    current_prices = {t: s.price for t, s in watchlist.items()}
    picked = result.get("picked_stock")
    action = result.get("picked_action")
    ratings = result.get("ratings", {})
    trade = result.get("trade_result")
    message = result.get("message", "")

    # Determine current node for flow display
    if trade:
        current_node = "Update" if not is_incremental else "Assess"
    elif picked:
        current_node = "Trade"
    elif ratings:
        current_node = "Research"
    else:
        current_node = "END"

    panels = []

    # State flow
    panels.append(display.show_state_flow(current_node, is_incremental))

    # Watchlist and Portfolio side by side
    watchlist_table = display.show_watchlist(watchlist, picked)
    portfolio_table = display.show_portfolio(portfolio, current_prices)

    panels.append(Columns([watchlist_table, portfolio_table], equal=True, expand=True))

    # Research ratings
    if ratings:
        panels.append(display.show_research(ratings, picked, action))

    # Trade result
    if trade:
        panels.append(display.show_trade(trade))

    # Status message
    if message:
        panels.append(Panel(f"[bold]{message}[/bold]", border_style="dim"))

    return panels


def main():
    display = DisplayService()

    # Show banner
    console.print(Panel(
        "[bold blue]╔══════════════════════════════════════╗[/bold blue]\n"
        "[bold blue]║[/bold blue]  [bold yellow]UC3 Stock Trading Simulator[/bold yellow]        [bold blue]║[/bold blue]\n"
        "[bold blue]║[/bold blue]  [dim]LangGraph + Rich Terminal UI[/dim]       [bold blue]║[/bold blue]\n"
        "[bold blue]║[/bold blue]  [dim]Design Patterns: Controller,[/dim]       [bold blue]║[/bold blue]\n"
        "[bold blue]║[/bold blue]  [dim]Builder, Creator, Expert[/dim]           [bold blue]║[/bold blue]\n"
        "[bold blue]╚══════════════════════════════════════╝[/bold blue]",
        border_style="blue",
    ))

    choice = display.show_menu()
    if choice == 5:
        console.print("[yellow]Goodbye![/yellow]")
        return

    # Initialize
    portfolio = Portfolio(account=Account(balance=INITIAL_FUNDS))
    watchlist = {t: Stock(t, t, p) for t, p in INITIAL_WATCHLIST.items()}
    market = MarketSimulator()

    is_incremental = choice in (2, 4)
    mode = "ai" if choice in (1, 2) else "manual"

    # Build the appropriate graph using Builder pattern
    if is_incremental:
        graph = build_incremental_graph()
    else:
        graph = build_conventional_graph()

    mode_label = "AI Automated" if mode == "ai" else "Manual"
    process_label = "Incremental" if is_incremental else "Conventional"
    console.print(f"\n[bold purple]Running: {process_label} Process — {mode_label}[/bold purple]")
    console.print(f"[dim]Prices update every {PRICE_UPDATE_INTERVAL}s. Press Ctrl+C to stop.[/dim]\n")

    round_num = 0
    try:
        while True:
            round_num += 1
            console.rule(f"[bold blue]Round {round_num}[/bold blue]")

            # Update prices
            market.update_prices(watchlist)

            current_prices = {t: s.price for t, s in watchlist.items()}

            # Build state
            if is_incremental:
                state = {
                    "watchlist": watchlist,
                    "portfolio": portfolio,
                    "ratings": {},
                    "picked_stock": None,
                    "picked_action": None,
                    "trade_result": None,
                    "message": "",
                    "mode": mode,
                    "display": display,
                    "remaining_shares": 0,
                    "total_shares": 0,
                    "increment_step": 0,
                    "continue_trading": False,
                    "price_at_start": 0.0,
                    "market_simulator": market,
                }
            else:
                state = {
                    "watchlist": watchlist,
                    "portfolio": portfolio,
                    "ratings": {},
                    "picked_stock": None,
                    "picked_action": None,
                    "trade_result": None,
                    "message": "",
                    "mode": mode,
                    "display": display,
                }

            # Run the LangGraph
            result = graph.invoke(state)

            # Display everything
            panels = build_display_layout(display, watchlist, portfolio, result, is_incremental)
            for panel in panels:
                console.print(panel)

            # Summary line
            total_value = portfolio.get_total_market_value(current_prices)
            pnl = total_value - INITIAL_FUNDS
            pnl_color = "green" if pnl >= 0 else "red"
            console.print(
                f"\n[bold]Portfolio Value:[/bold] [yellow]${total_value:,.2f}[/yellow]  "
                f"[bold]P/L:[/bold] [{pnl_color}]${pnl:+,.2f}[/{pnl_color}]  "
                f"[bold]Cash:[/bold] [yellow]${portfolio.account.balance:,.2f}[/yellow]\n"
            )

            # Wait
            if mode == "ai":
                console.print(f"[dim]Next round in {PRICE_UPDATE_INTERVAL}s...[/dim]")
                time.sleep(PRICE_UPDATE_INTERVAL)
            else:
                input_text = console.input("[yellow]Press Enter for next round (or 'q' to quit): [/yellow]")
                if input_text.strip().lower() == "q":
                    break

    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped by user. Final state:[/yellow]")
        current_prices = {t: s.price for t, s in watchlist.items()}
        console.print(display.show_portfolio(portfolio, current_prices))


if __name__ == "__main__":
    main()
