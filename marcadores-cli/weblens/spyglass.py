# 
# filename:     spyglass.py
# description:  contains all the necessary functions to access
#               the scoreboard
#

import requests
from bs4 import BeautifulSoup

import config

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

