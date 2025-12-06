# 
# filename:     spyglass.py
# description:  contains all the necessary functions to access
#               the scoreboard
#

from bs4 import BeautifulSoup

from . import config
from . import rendering
from . import containers

import re
import json

def get_sports_list() -> list[str]:
    """
    Looks for the available sports in the webpage, using the class
    identifier from the HTML file
    """
    sports = []

    soup = rendering.get_soup(config.FS_URL)

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
    soup = rendering.get_soup(sport_url)

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
    soup = rendering.get_soup(sport_country_url)

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

    # URL
    results_url = f"{config.FS_URL}/{sport}/{country}/{league}/results/"

    soup = rendering.get_soup(results_url)
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


def get_league_raw_soup(sport: str, country: str, league: str)-> BeautifulSoup:
    """
    Docstring for get_league_raw_soup

    :param sport: Sport from which you want to extract the soup from
    :type sport: str
    :param country: Country from which you want to extract the soup from
    :type country: str
    :param league: league from which you want to extract the soup from
    :type league: str
    :return: Raw Soup Object of the standings HTML, with the JS loaded
    :rtype: BeautifulSoup
    """
    standings_url = f"{config.FS_URL}/{sport}/{country}/{league}/standings/"

    # We extract the rederized HTML
    league_raw_soup = rendering.get_soup(standings_url, "#tournament-table")

    return league_raw_soup


def get_standings(sport: str, country: str, league: str):
    """
    Get function to obtain the current standings table for a league.
    """
    standings = []

    soup = get_league_raw_soup(sport, country, league)

    table = soup.find("div", id=config.ID_TABLE)
    rows = table.find_all("div", class_=config.CLASS_ROWSTANDING)

    # We go row by row extracting: name, rank and points
    for row in rows:
        name_tag = row.find(class_=config.CLASS_NAMEROW)

        if not name_tag:
            continue

        name = name_tag.get_text(strip=True)
        rank = row.find("div", class_=config.CLASS_RANKROW).get_text()

        points_tag = row.find(class_=config.CLASS_POINTSROW)

        # !TODO: For instance in NBA there are no points. Just W / L
        #        Here would be nice a good treatment of errors and
        #        exceptions. "get_text()" pops up an error if it is
        #        None
        if points_tag is not None:
            points = points_tag.get_text()
        else:
            points = ""

        standings.append({
            "rank": rank,
            "team": name,
            "points": points,
        })

    return standings

def get_teams_league(sport: str, country: str, league: str):
    """
    Get function to obtain the current teams of a league. The resulting
    list comes ordered by the points. 0 has the most points.
    """
    teams = []

    # Standings contain: rank, team & points
    standings = get_standings(sport, country, league)

    # We extract only the 'team' key
    for row in standings:
        teams.append(row['team'])

    return teams


def get_team_keynames(sport: str, country: str, league: str):
    """
    Get function to obtain the keynames of the teams in a league.
    The keynames are the team names used in the CLI.
    """
    teams_keynames = []

    # This RE means: team/ followed for whatever (unless it's /) and
    # then another / followed for whatever
    KEYNAME_RE = r'team/([^/]+)/*'

    soup = get_league_raw_soup(sport, country, league)

    table = soup.find("div", id=config.ID_TABLE)
    rows = table.find_all("div", class_=config.CLASS_ROWSTANDING)

    # We go row by row extracting the keyname
    for row in rows:
        name_tag = row.find(class_=config.CLASS_NAMEROW)

        if not name_tag:
            continue

        href_team = name_tag.get("href")

        match_re = re.search(r"/team/([^/]+)/", href_team)

        if match_re:
            # The Match would have 3 groups:
            #   - group(0): team
            #   - group(1): team_keyname
            #   - group(2): team_id
            teams_keynames.append(match_re.group(1))

    return teams_keynames


def get_team_id(sport: str, country: str, league: str, team: str) -> str:
    """
    Get function to obtain a certain team's ID
    """
    soup = get_league_raw_soup(sport, country, league)

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

    # We extract the rederized HTML
    soup = rendering.get_soup(team_url, f".{config.CLASS_SCHEDULED}")

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

    # We extract the rederized HTML
    soup = rendering.get_soup(results_url,
                              f".{config.CLASS_LEAGUE_TAG}")

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


def get_news_sections() -> list[dict]:
    """
    Docstring for get_news_sections

    :return: A list of dictionaries that contains two keys: name and url
    of the sections of news available.
    :rtype: list[dict]
    """
    sections = []

    # News URL
    news_url = f"{config.FS_URL}/news"

    soup = rendering.get_soup(news_url)

    # We get the script tags that loads by js
    script_tags = soup.find_all('script', type="text/javascript")

    # We select the tag that matches de regular expression
    for tag in script_tags:
        script_text = tag.get_text()
        dropdown_re = r'window.fsNewsMenuData'

        if re.match(dropdown_re, script_text):
            dropdown_tag = tag

    match = re.search(r"window\.fsNewsMenuData\s*=\s*(\{.*\})",
                      dropdown_tag.get_text())

    # The match.group(1) is the JSON that loads by the JS
    json_news_section = match.group(1)
    data_section = json.loads(json_news_section)

    # The JSON has the menu key, which is what we want
    for section in data_section['data']['menu']:
        # Corner case
        if section['name'] == 'TRANS_FSNEWS_ALL':
            section_name = 'All'
        # General case
        else:
            section_name = section['name']

        sections.append({
            "name": section_name,
            "url": section['url']
        })

    return sections


def get_news(section: str) -> list[containers.Article]:
    """
    Get functionality that allows you to obtain the news from your
    desired section/sport.

    :param section: Description
    :type section: str
    :return: Description
    :rtype: list[Article]
    """
    news = []
    partial_section_url = None

    available_sections = get_news_sections()

    for isection in available_sections:
        if isection['name'] == section:
            partial_section_url = isection['url']

    # !TODO: Another case of error handling
    if partial_section_url is None:
        print("Unknown section")
        return -1

    # Obtaining URL + Soup
    section_url = config.FS_URL + partial_section_url
    soup_news = rendering.get_soup(section_url)

    news_tag = soup_news.find_all(class_=config.CLASS_NEWSSECTION)

    # We are going trough the different news tags
    for tag in news_tag:
        # We avoid general news
        if config.CLASS_MISCNEWS not in tag.get("class"):
            for inner_tag in tag.contents:
                article_identifier = inner_tag.get("data-testid")

                # We choose only articles
                if article_identifier == config.DATA_TESTID_ARTICLES:
                    article = containers.Article(title=inner_tag.get("title"),
                                                 url=inner_tag.get("href"),
                                                 )
                    date_tag = inner_tag.find("span")

                    # Not all the article have date
                    if date_tag is not None:
                        date_text = date_tag.get_text()
                        article.set_date(date_text)

                    news.append(article)

    return news
