# 
# filename:     spyglass.py
# description:  contains all the necessary functions to access
#               the scoreboard
#

import requests

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from bs4 import BeautifulSoup

from . import config

import time
import re

def get_sports_list() -> list[str]:
    """
    Looks for the available sports in the webpage, using the class
    identifier from the HTML file
    """
    sports = []

    # Obtain page & soup
    main_page = requests.get(config.FS_URL)
    soup = BeautifulSoup(main_page.content, "html.parser")

    # Obtain all the main sports via the class identifier
    main_sports_tag = soup.find_all(class_=config.ID_MAIN_SPORTS)

    # Fill our list
    for tag in main_sports_tag:
        sports.append(tag.get_text(strip=True))

    #!TODO: Add the secondary sports, create special case for
    #       'Favourites'

    return sports


#!TODO: Bug detected in this functionality, does not work correctly
#       ID from the find_all must be changed. Might be
#       lmc__elementName or smth like that (?)
def get_league_countries(sport: str) -> list[str]:
    """
    Get function to see available countries and leagues within an sport
    """
    countries = []

    # Obtain page & soup
    sport_url = config.FS_URL + "/" + sport
    #!TODO: Check whether the sport is correct or not. Investigate how
    #       handle errors and expections
    sport_page = requests.get(sport_url)
    soup = BeautifulSoup(sport_page.content, "html.parser")

    # Obtain first div element of HTML
    countries_tag = soup.find_all(class_=config.ID_MAIN_COUNTRIES)

    # Go through the div adding the different countries and leagues
    for c in countries_tag[0].find_all(True):
        countries.append(c.get_text(strip=True))

    return countries


def get_reg_leagues(sport: str, country: str) -> list[str]:
    """
    Get function to see available regional leagues within a country
    """
    reg_leagues = []

    # Obtain page & soup
    sport_country_url = config.FS_URL + "/" + sport + "/" + country

    #!TODO: Same... before arguments shall be checked, and they
    #       might shall not pass!
    sport_coutry_page = requests.get(sport_country_url)
    soup = BeautifulSoup(sport_coutry_page.content, "html.parser")

    reg_leagues_tag = soup.find_all(class_=config.ID_MAIN_REG_LEAGUES)

    # Go through the tag checking the different reg_leagues
    for rl in reg_leagues_tag:
        reg_leagues.append(rl.get_text(strip=True))

    #!TODO: This is returned as the string without any kind of treatment
    #       If this array is used, each string will be needed to be
    #       reshaped
    #
    #       i.e: 'Primera RFEF - Group 2' --> 'primera-rfef-group-2'
    #
    return reg_leagues


def get_results(sport: str, country: str, league: str, round: int = 0):
    """
    Get function to obtain the results of all the games in a
    specific round.
    """
    games = [ ]

    # Configure Chrome
    options = Options()
    options.add_argument("--headless=new")        # No window popping-up

    # We run Chrome
    driver = webdriver.Chrome(options=options)

    # URL
    results_url = f"{config.FS_URL}/{sport}/{country}/{league}/results/"

    driver.get(results_url)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    # !TODO: Investigate a method / functionality to know if the JS
    #        has been loaded completely

    # Find all the games
    round_tag = soup.find_all(class_=config.ID_ROUND)
    # !TODO: Correct if list index "round" is out of range and invert it
    # so it fits

    # ------------------------------------------------------------------
    # Take the first match...
    #
    #   If we navigate the HTML tree, the "event__round" div, is at the
    #   same level as the rest of the games ("event__match" div), then
    #   they are siblings.
    #
    #   We are going to navigate the tree until we find another round.
    #   Here there is a little schema about it:
    #
    #         > HTML TREE <
    #
    #   <div class="event__round">       // Here starts 1 round
    #   <div class="event__match">       // Below... all the games
    #               ·
    #               ·
    #               ·
    #   <div class="event__match">
    #   <div class="event__round">      // Here starts another round
    #                                   // We stop!
    #
    # ------------------------------------------------------------------
    cmatch = round_tag[round].find_next_sibling()

    while(cmatch.get("class")[0] == config.ID_MATCHROW):
        # We get local team and score
        local_team = cmatch.find(class_=config.ID_LOCALTEAM).get_text()
        local_score = cmatch.find(class_=config.ID_LOCALSCORE).get_text()

        local_data = {"team": local_team, "score": local_score}

        # We get away team and score
        away_team = cmatch.find(class_=config.ID_AWAYTEAM).get_text()
        away_score = cmatch.find(class_=config.ID_AWAYSCORE).get_text()

        away_data = {"team": away_team, "score": away_score}

        # Join up data in a single tuple
        game_data = (local_data, away_data)

        games.append(game_data)
        cmatch = cmatch.find_next_sibling()

    return games


def get_standings(sport: str, country: str, league: str):
    """
    Get function to obtain the current standings table for a league.
    """
    standings = []

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=options)

    standings_url = f"{config.FS_URL}/{sport}/{country}/{league}/standings/"
    driver.get(standings_url)

    # Wait until our selected table js's is loaded
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                                            "#tournament-table"))
        )
    except TimeoutException:
        driver.quit()
        return standings

    # Wait some extraseconds
    time.sleep(2)

    # We extract the rederized HTML
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    table = soup.find("div", id=config.ID_TABLE)
    rows = table.find_all("div", class_=config.CLASS_ROWSTANDING)

    # We go row by row extracting: name, rank and points
    for row in rows:
        name_tag = row.find(class_=config.CLASS_NAMEROW)

        if not name_tag:
            continue

        name = name_tag.get_text(strip=True)
        rank = row.find("div", class_=config.CLASS_RANKROW).get_text()
        points = row.find(class_=config.CLASS_POINTSROW).get_text()

        standings.append({
            "rank": rank,
            "team": name,
            "points": points,
        })

    return standings


def get_team_id(sport: str, country: str, league: str, team: str) -> str:
    """
    Get function to obtain a certain team's ID
    """

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=options)

    standings_url = f"{config.FS_URL}/{sport}/{country}/{league}/standings/"
    driver.get(standings_url)

    # Wait until our selected table js's is loaded
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                                            "#tournament-table"))
        )
    except TimeoutException:
        driver.quit()
        return

    # Wait some extraseconds
    time.sleep(2)

    # We extract the rederized HTML
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    table = soup.find("div", id=config.ID_TABLE)
    rows = table.find_all("div", class_=config.CLASS_ROWSTANDING)

    # We go row by row checking if the team is found
    for row in rows:
        url_tag = row.find(class_=config.CLASS_NAMEROW)

        splitted_team_href = re.split("/", url_tag.get("href"))

        # splitted_team_href example:
        #
        #  0   1       2                         3
        # ['', 'team', 'minnesota-timberwolves', 'KjBIVQcI', '']
        #

        if splitted_team_href[2] == team:
            return splitted_team_href[3]

    #!TODO: Add a corner case if team is not found


# !TODO: Change how this internally works and use the "fixtures" subpage
# !TODO: Add documentation
def get_team_next_games(sport: str, country: str, league: str, team: str):
    next_games = [ ]

    # We need the id...
    team_id = get_team_id(sport, country, league, team)
    # To create the url
    team_url = f"{config.FS_URL}/team/{team}/{team_id}"

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=options)
    driver.get(team_url)

    # Wait until our selected table js's is loaded
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                                            f".{config.CLASS_SCHEDULED}"))
        )
    except TimeoutException:
        driver.quit()
        return

    # Wait some extraseconds
    time.sleep(2)

    # We extract the rederized HTML
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    section_tags = soup.find_all(class_=config.ID_SECTION)

    # If we find the 'Scheduled' section...
    for i, x in enumerate(section_tags):
        if x.get_text() == config.SECTION_SCHEDULED:
            scheduled_tag = section_tags[i]

    if scheduled_tag == None:
        print("No scheduled matches found")
        return

    scheduled_matches = scheduled_tag.next_sibling.find_all(
                                            class_=config.CLASS_SCHEDULED)

    # ... we iterate through it, getting the time and teams
    for scheduled_match in scheduled_matches:
        match_time = scheduled_match.find(
            class_=config.CLASS_TIME).get_text()

        local_team = scheduled_match.find(
            class_=config.CLASS_HOME_TEAM_SCHEDULED).get_text()

        away_team = scheduled_match.find(
            class_=config.CLASS_AWAY_TEAM_SCHEDULED).get_text()

        next_games.append((match_time, (local_team, away_team)))

    return next_games

def get_team_prev_games(sport: str, country: str, league: str, team: str):
    """
    Get functionality to obtain all the previous games of a certain
    team.
    """
    prev_games = []

    # We need the id...
    team_id = get_team_id(sport, country, league, team)
    # To create the url
    team_url = f"{config.FS_URL}/team/{team}/{team_id}"
    results_url = f"{team_url}/results"

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=options)
    driver.get(results_url)

    # Wait until our selected table js's is loaded
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                                            f".{config.CLASS_LEAGUE_TAG}"))
        )
    except TimeoutException:
        driver.quit()
        return

    # Wait some extraseconds
    time.sleep(2)

    # We extract the rederized HTML
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    # print(soup)

    # This is the overall section
    league_event_section = soup.find(class_=config.CLASS_LEAGUE_TAG)

    # There are league divs...
    class_id_league = "headerLeague__wrapper"
    # ... and event divs
    class_id_event  = "event__match"
    iterator_league = -1

    # For each div...
    for row in league_event_section.children:
        class_row = row.get("class")

        # We select if it's either league...
        if class_id_league in class_row:
            iterator_league = iterator_league + 1
            league = row.find(class_=config.CLASS_HEADER_LEAGUE).get_text()
            prev_games.append((league, []))

        # Or event!
        elif class_id_event in class_row:
            home_team = row.find(class_=config.CLASS_HOME_TEAM_SCHEDULED).get_text()
            home_score = row.find(class_=config.ID_LOCALSCORE).get_text()
            away_team = row.find(class_=config.CLASS_AWAY_TEAM_SCHEDULED).get_text()
            away_score = row.find(class_=config.ID_AWAYSCORE).get_text()
            date = row.find(class_=config.CLASS_TIME).get_text()

            event = (date, ((home_team, home_score),(away_team, away_score)))

            prev_games[iterator_league][1].append(event)

    ###########---prev_games data-structure---##########################
    #
    # The structure of the divs are more or less like this:
    #
    #   [league]
    #       |-----[event]~ (date, ((home_team, home_score), [event],...
    #       |                     (away_team, away_score)))
    #       ·
    #       ·
    #   [league]
    #       |-----[event]~ (date, ((home_team, home_score), [event],...
    #       |                     (away_team, away_score)))
    #
    #-------------------------------------------------------------------
    #
    # For example: Here you can iterate through the whole data structure
    # for league, events in prev_games:
    #     print(f"league: {league}")
    #
    #     for event in events:
    #         print(f"date: {event[0]}")
    #         print(f"home_team:{event[1][0][0]} home_score:{event[1][0][1]}")
    #         print(f"away_team:{event[1][1][0]} away_score:{event[1][1][1]}")
    #

    return prev_games
