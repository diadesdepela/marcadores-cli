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


@click.command("list_of_sports")
def list_of_sports() -> None:
    """
    List of sports available to show.
    """
    sports = spyglass.get_sports_dict()

    list_msg = f"List of sports\n"

    for url, sport in sports.items():
        list_msg = list_msg + f"\t{sport} - {url}\n"

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


@click.command("get_reg_league")
@click.argument("sport", required=True, nargs=1)
@click.argument("country", required=True, nargs=1)
def get_reg_league(sport: str, country: str) -> None:
    """
    Lists the available regional leagues for a country's sport
    """

    # We obtain the list and start building the message
    reg_league_list = spyglass.get_reg_leagues(sport, country)
    reg_league_msg = f"Available regional {sport} leagues located in {country}\n"

    for reg_league in reg_league_list:
        reg_league_msg = reg_league_msg + f"\t{reg_league}\n"

    console.print(
        f"{reg_league_msg}"
    )

    return None


# !TODO: Add option -S / -s to --save the the configuration
#        Some steps into creating a saving marcadores.config
@click.command("get_results")
@click.argument("sport", required=True, nargs=1)
@click.argument("country", required=True, nargs=1)
@click.argument("league", required=True, nargs=1)
@click.option("-r", "--round", required=False, nargs=1, type=click.INT,
              show_default=True)
def get_results(sport: str, country: str, league: str,
                   round: int = 0) -> None:
    """
    Lists the table of results of an specific round in a league of a
    country and sport
    """

    if round is None:
        round = 0

    # We obtain the result list
    results = spyglass.get_results(sport, country, league, round)

    # !TODO: Normalize the round number to the actual one. Probably
    #        a "get_last_round_number" function or similar has to be
    #        made
    reg_league_msg = f"Results of round {round} in {league}:\n"

    # [0] -> Always local/home
    # [1] -> Always away
    local_result = 0
    away_result = 1

    # !TODO: Some stylizing could be done using rich, at least to make 
    # all the scores in a "straight line"
    for result in results:
        local_team = f"{result[local_result]["team"]}"
        local_score = f"{result[local_result]["score"]}"
        local_msg = f"\t{local_team}: {local_score}"

        away_team = f"{result[away_result]["team"]}"
        away_score = f"{result[away_result]["score"]}"
        away_msg = f" - {away_score} :{away_team}\n"

        reg_league_msg = reg_league_msg + local_msg + away_msg

    console.print(
        f"{reg_league_msg}"
    )

    return None


@click.command("get_standings")
@click.argument("sport", required=True)
@click.argument("country", required=True)
@click.argument("league", required=True)
def get_standings(sport: str, country: str, league: str)-> None:
    """
    Prints the current standings table for a league.
    """

    standings = spyglass.get_standings(sport, country, league)

    standings_msg = f"Standings for {league}\n"

    for rank in standings:
        position = rank["rank"]
        team = rank["team"]
        points = rank["points"]

        standings_msg = standings_msg + f"\t{position} {team} - {points}\n"

    console.print(
        f"{standings_msg}"
    )

    return None

@click.command("get_team_games")
@click.argument("sport", required=True)
@click.argument("country", required=True)
@click.argument("league", required=True)
@click.argument("team", required=True)
@click.option("-t", "--time",
              type=click.Choice(["next", "last"], case_sensitive=False),
              default="last",
              help="Select whether you want planned or already playe games"
              )
def get_team_games(sport: str, country: str, league: str, team: str,
                    time: str) -> None:
    """
    Lists the past or following games of a team
    """
    date_ = 0
    teams_ = 1

    local_team_ = 0
    away_team_ = 1

    team_name_ = 0
    team_score = 1

    if time == "last":
        team_league_games = spyglass.get_team_prev_games(sport, country,
                                                            league, team)
        g_msg = f"Last games of {team}:\n"

        for league_games in team_league_games:
            g_msg = g_msg + f"\tLeague - {league_games[0]}\n"

            for games in league_games[1]:
                g_msg = g_msg + f"\t\t{games[date_]}- " \
                                f"{games[teams_][local_team_][team_name_]}> " \
                                f"{games[teams_][local_team_][team_score]} | "\
                                f"{games[teams_][away_team_][team_score]} <"  \
                                f"{games[teams_][away_team_][team_name_]}\n"
    else:
        team_games = spyglass.get_team_next_games(sport, country, league, team)
        g_msg = f"Next games of {team} in {league}:\n"

        for game in team_games:
            g_msg = g_msg + f"\t{game[date_]}- {game[teams_][local_team_]}"\
                                    f" vs. {game[teams_][away_team_]}\n"

    console.print(
        f"{g_msg}"
    )

    return None


#//////////////////////////////////////////////////////////////////////#
#//////////////////////////////////////////////////////////////////////#

marcadorescli.add_command(list_of_sports)
marcadorescli.add_command(get_leagues_countries)
marcadorescli.add_command(get_reg_league)
marcadorescli.add_command(get_results)
marcadorescli.add_command(get_standings)
marcadorescli.add_command(get_team_games)

if __name__ == "__main__":
    marcadorescli()
