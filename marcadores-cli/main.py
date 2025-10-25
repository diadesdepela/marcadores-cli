from weblens import spyglass

import click

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

console = Console()


@click.group()
def marcadorescli():
    """CLI Main Entry point"""
    pass


@click.command()
def manual() -> None:
    """Personalized help"""

    # Creates the table with: Commands | Description columns
    manual_table = Table(title="Usage of Marcadores CLI")
    manual_table.add_column("[bold]Command[/bold]", justify="center")
    manual_table.add_column("[bold]Description[/bold]", justify="center")

    # Start adding rows to the table
    manual_table.add_row("[bold]manual[/bold]", 
                         "Shows a personalized [bold]rich[/bold]er help",)
    manual_table.add_section()
    manual_table.add_row("[bold]list-of-sports[/bold]",
                         "Lists the available sports for the CLI")

    # Print the table
    console.print(
        Panel(
            manual_table,
            title="> HELP <",
            border_style="blue",
        )
    )



# TODO: This will be done dinamically through the webpage, this is
#       only a WIP to try out commands
@click.command("list-of-sports")
def list_of_sports() -> None:
    """
    List of sports available to show.
    This a WIP, it will be dynamically listed.
    """
    console.print(
        Panel(
            "[bold]Available sports:[/bold]\n\t- Football\n\t- Tennis " \
            "\n\t- Basketball",
            title="Sports List",
            border_style="blue",
        )
    )


marcadorescli.add_command(manual)
marcadorescli.add_command(list_of_sports)


if __name__ == "__main__":
    marcadorescli()
