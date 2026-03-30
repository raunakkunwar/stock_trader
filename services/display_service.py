import math
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.columns import Columns

from models.stock import Stock
from models.portfolio import Portfolio
from models.transaction import Transaction


console = Console()


class DisplayService:
    """Colorful terminal UI using rich library."""

    def __init__(self):
        self.console = console

    def show_menu(self) -> int:
        self.console.print()
        self.console.print(Panel(
            "[bold blue]UC3 Stock Trading Simulator[/bold blue]\n\n"
            "[yellow]1.[/yellow] Conventional Process — AI Automated\n"
            "[yellow]2.[/yellow] Iterative Incremental Process — AI Automated\n"
            "[yellow]3.[/yellow] Conventional Process — Manual\n"
            "[yellow]4.[/yellow] Iterative Incremental Process — Manual\n"
            "[yellow]5.[/yellow] Exit\n",
            title="[bold purple]Main Menu[/bold purple]",
            border_style="blue",
        ))
        while True:
            try:
                choice = int(self.console.input("[yellow]Select option (1-5): [/yellow]"))
                if 1 <= choice <= 5:
                    return choice
            except (ValueError, EOFError):
                pass
            self.console.print("[red]Invalid choice. Try again.[/red]")

    def show_watchlist(self, watchlist: dict[str, Stock], picked: str = None) -> Table:
        """Green up arrow for up, Red down arrow for down, yellow star for picked stock."""
        table = Table(title="[bold blue]Market Watchlist[/bold blue]", border_style="blue")
        table.add_column("Ticker", style="bold", width=8)
        table.add_column("Price", justify="right", width=12)
        table.add_column("Change", justify="right", width=10)
        table.add_column("", width=3)

        for ticker, stock in watchlist.items():
            change = stock.change_pct
            if change > 0:
                arrow = "[green]▲[/green]"
                change_str = f"[green]+{change:.2f}%[/green]"
            elif change < 0:
                arrow = "[red]▼[/red]"
                change_str = f"[red]{change:.2f}%[/red]"
            else:
                arrow = "[dim]—[/dim]"
                change_str = f"[dim]0.00%[/dim]"

            star = " [yellow]★[/yellow]" if ticker == picked else ""
            table.add_row(
                f"{ticker}{star}",
                f"${stock.price:,.2f}",
                change_str,
                arrow,
            )
        return table

    def show_portfolio(self, portfolio: Portfolio, prices: dict) -> Table:
        table = Table(title="[bold blue]Portfolio[/bold blue]", border_style="green")
        table.add_column("Ticker", style="bold", width=8)
        table.add_column("Shares", justify="right", width=8)
        table.add_column("Avg Cost", justify="right", width=12)
        table.add_column("Mkt Value", justify="right", width=12)
        table.add_column("P/L", justify="right", width=12)

        for ticker, pos in portfolio.holdings.items():
            price = prices.get(ticker, pos.avg_cost)
            mkt_value = pos.shares * price
            pl = mkt_value - pos.total_cost
            pl_color = "green" if pl >= 0 else "red"
            table.add_row(
                ticker,
                str(pos.shares),
                f"${pos.avg_cost:,.2f}",
                f"${mkt_value:,.2f}",
                f"[{pl_color}]${pl:+,.2f}[/{pl_color}]",
            )

        table.add_section()
        total_value = portfolio.get_total_market_value(prices)
        table.add_row(
            "[bold]Cash[/bold]", "", "", f"[yellow]${portfolio.account.balance:,.2f}[/yellow]", ""
        )
        table.add_row(
            "[bold]Total[/bold]", "", "", f"[bold yellow]${total_value:,.2f}[/bold yellow]", ""
        )
        return table

    def show_research(self, ratings: dict, picked: str, action: str) -> Panel:
        lines = []
        for ticker, rating in ratings.items():
            if rating == "BUY":
                lines.append(f"  [green]{ticker}: BUY[/green]")
            elif rating == "SELL":
                lines.append(f"  [red]{ticker}: SELL[/red]")
            else:
                lines.append(f"  [dim]{ticker}: HOLD[/dim]")

        if picked:
            action_color = "green" if action == "BUY" else "red"
            lines.append(f"\n  [yellow]★ Pick: [{action_color}]{action} {picked}[/{action_color}][/yellow]")
        else:
            lines.append(f"\n  [dim]No actionable picks this round.[/dim]")

        return Panel(
            "\n".join(lines),
            title="[bold blue]AI Research[/bold blue]",
            border_style="purple",
        )

    def show_trade(self, transaction: Transaction) -> Panel:
        order = transaction.trade_order
        if transaction.status == "FILLED":
            color = "green" if order.side == "BUY" else "red"
            content = (
                f"  [{color}]{order.side}[/{color}] {order.quantity} x {order.ticker} "
                f"@ ${order.price_at_order:,.2f}\n"
                f"  Total: [yellow]${order.total:,.2f}[/yellow]\n"
                f"  Status: [green]FILLED[/green]\n"
                f"  ID: [dim]{transaction.id}[/dim]"
            )
        else:
            content = (
                f"  {order.side} {order.quantity} x {order.ticker} "
                f"@ ${order.price_at_order:,.2f}\n"
                f"  Status: [red]REJECTED[/red]\n"
                f"  ID: [dim]{transaction.id}[/dim]"
            )
        return Panel(content, title="[bold blue]Trade Result[/bold blue]", border_style="yellow")

    def show_state_flow(self, current_node: str, is_incremental: bool = False) -> Panel:
        """Shows: START -> Research -> Pick? -> Trade -> Update -> END
        with current node highlighted."""
        if is_incremental:
            nodes = ["START", "Research", "Pick?", "Trade", "Assess", "Continue?", "END"]
        else:
            nodes = ["START", "Research", "Pick?", "Trade", "Update", "END"]

        parts = []
        for node in nodes:
            if node.lower().replace("?", "") == current_node.lower().replace("?", ""):
                parts.append(f"[bold purple][ {node} ][/bold purple]")
            else:
                parts.append(f"[dim]{node}[/dim]")

        flow = " → ".join(parts)
        return Panel(flow, title="[bold purple]LangGraph State Flow[/bold purple]", border_style="purple")

    def show_incremental_step(self, step: int, shares: int, total_shares: int,
                               assessment: str) -> Panel:
        content = (
            f"  Step [yellow]{step}[/yellow]: traded [bold]{shares}[/bold] shares\n"
            f"  Remaining: [bold]{total_shares}[/bold] shares\n"
            f"  Assessment: {assessment}"
        )
        return Panel(content, title="[bold blue]Incremental Step[/bold blue]", border_style="blue")

    def prompt_stock_selection(self, watchlist: dict[str, Stock],
                                portfolio: Portfolio) -> tuple[str | None, str | None]:
        """Manual mode: prompt user to select a stock and action."""
        self.console.print("\n[yellow]Available tickers:[/yellow]", ", ".join(watchlist.keys()))
        ticker = self.console.input("[yellow]Enter ticker (or 'skip' to skip): [/yellow]").strip().upper()
        if ticker == "SKIP" or ticker not in watchlist:
            return None, None

        self.console.print(f"\n[yellow]Selected: {ticker} @ ${watchlist[ticker].price:,.2f}[/yellow]")
        pos = portfolio.get_position(ticker)
        if pos:
            self.console.print(f"[dim]You own {pos.shares} shares[/dim]")

        action = self.console.input("[yellow]Action (BUY/SELL): [/yellow]").strip().upper()
        if action not in ("BUY", "SELL"):
            return None, None

        return ticker, action
