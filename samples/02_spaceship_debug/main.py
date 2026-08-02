"""宇宙船の診断結果を見やすく表示する。"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from spaceship import Spaceship, average_sensor_reading, demo_ship


def status(value: bool) -> str:
    return "[green]PASS[/green]" if value else "[bold red]FAIL[/bold red]"


def build_diagnostics(ship: Spaceship) -> Table:
    table = Table(title=f"{ship.name} // PRE-FLIGHT DIAGNOSTICS", border_style="cyan")
    table.add_column("SYSTEM", style="bold")
    table.add_column("READING", justify="right")
    table.add_column("STATUS", justify="center")
    table.add_row("Fuel", f"{ship.fuel:.1f}%", status(0 <= ship.fuel <= 100))
    table.add_row("Oxygen", f"{ship.oxygen:.1f}%", status(0 <= ship.oxygen <= 100))
    table.add_row("Hull", f"{ship.hull:.1f}%", status(0 <= ship.hull <= 100))
    table.add_row("Reactor", f"{ship.reactor_temperature:.1f} °C", status(ship.reactor_online))
    return table


def main() -> None:
    console = Console()
    ship = demo_ship()
    console.print(build_diagnostics(ship))

    sensor_average = average_sensor_reading([315.5, 316.0, 315.8])
    console.print(f"Sensor fusion result: [bold]{sensor_average:.2f} °C[/bold]")
    if ship.ready_for_launch():
        console.print(Panel.fit("GO FOR LAUNCH", style="bold green"))
    else:
        console.print(Panel.fit("LAUNCH HOLD — RUN pytest", style="bold red"))
    console.print("\n[dim]次のコマンド: uv run pytest[/dim]")


if __name__ == "__main__":
    main()

