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


@click.command("list-of-sports")
def list_of_sports() -> None:
    """
    List of sports available to show.
    """
    sport_list = spyglass.get_sports_list()

    list_msg = f"List of sports\n"

    for sport in sport_list:
        list_msg = list_msg + f"   {sport}\n"

    console.print(
            f"{list_msg}"
    )

    return None


@click.command("get-leagues-countries")
@click.argument("sport", required=True, nargs=1)
@click.option("-l", "--letter", help="Pass a single character to filter out " \
                                     "the leagues shown based on the initial" \
                                     "letter", show_default=True)
def get_leagues_countries(sport: str, letter: str | None = None) -> None:
    """
    Lists the available countries or international leagues for a sport
    """

    # We check if the option is a single character string
    if letter is not None and len(letter) > 1:
        print("Argumental error: The letter filter must be "
              "single character\r\n")
        click.help_option()

    # We obtain the list and start building the message
    league_list = spyglass.get_league_countries(sport)
    league_msg = f"Available leagues & countries for {sport}\n"

    if letter is not None:
        for league in league_list:
            if letter.lower() == league[0].lower():
                    league_msg = league_msg + f"   {league}\n"
    else:
        for league in league_list:
            league_msg = league_msg + f"   {league}\n"

    console.print(
        f"{league_msg}"
    )

    return None


marcadorescli.add_command(list_of_sports)
marcadorescli.add_command(get_leagues_countries)

if __name__ == "__main__":
    marcadorescli()
