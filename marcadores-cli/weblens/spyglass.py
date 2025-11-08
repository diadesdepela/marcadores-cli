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

import config
import time

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
