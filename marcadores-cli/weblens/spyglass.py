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

def get_sports_dicts() -> tuple[dict, dict]:
    """
    Get funcitonality that allows you to see the available sports in
    the website

    :return: The available sports. Dictionary. Key: url, value: name of
    the sport
    :rtype: dict
    """
    main_sports = {}
    minority_sports = {}

    soup = rendering.get_soup(config.FS_URL)

    # Obtain all the main sports via the class identifier
    main_sports_tag = soup.find_all(class_=config.ID_MAIN_ITEMS)
    minority_sports_tag = soup.find_all(class_=config.ID_MINO_ITEMS)

    # Fill our main sport list
    for main_tag in main_sports_tag:
        main_sport_tag = main_tag.find(class_=config.ID_MAIN_SPORTS)

        if main_sport_tag:
            sport_text = main_sport_tag.get_text(strip=True)
            sport_href = main_tag.get("href")

            main_sports.update({sport_href: sport_text})

    # Fill our minority sport list
    for mino_tag in minority_sports_tag:
        mino_sport_tag = mino_tag.find(class_=config.ID_MINO_SPORTS)

        if mino_sport_tag:
            sport_text = mino_sport_tag.get_text(strip=True)
            sport_href = mino_tag.get("href")

            minority_sports.update({sport_href: sport_text})

    return main_sports, minority_sports


def get_league_countries(sport: str) -> tuple[dict, dict]:
    """
    Docstring for get_league_countries

    :param sport: Desired sport from where to obtain the different
    countries availables
    :type sport: str
    :return: Tuple that contains the countries and the competitions
    :rtype: tuple[dict, dict]
    """
    countries = {}
    competitions = {}

    # Obtain page & soup
    sport_url = config.FS_URL + "/" + sport
    soup = rendering.get_soup(sport_url)

    script_tags = soup.find_all('script')

    for tag in script_tags:
        script_text = tag.get_text()

        if (config.VAR_JSON_COUNTRIES in script_text and
            config.VAR_JSON_COUNTRIES in script_text):
            countries_tag = tag
            break

    # Regular expresion that follows the json inside the js variable
    rawdata_re = r'rawData\s*:\s*(\[\{.*?\}\]\}\])'

    match = re.search(rawdata_re, countries_tag.get_text(), flags=re.DOTALL)
    raw_json = match.group(1)

    raw_data = json.loads(raw_json)

    # There are two main parts: 'countries' and 'other competitions'
    for country in raw_data[0][config.DICT_KEY_COUNTRIES]:
        countries.update({country["ML"]: country["MCN"]})

    for competition in raw_data[1][config.DICT_KEY_COUNTRIES]:
        competitions.update({competition["ML"]: competition["MCN"]})

    return countries, competitions


def get_reg_leagues(sport: str, country: str) -> dict:
    """
    Get functionality to obtain a dictionary of all the leagues

    :param sport: Desired sport from where to obtain the leagues
    :type sport: str
    :param country: Desired country from where to obtain the leagues
    :type country: str
    :return: String dictionary of keyname_league, name_league
    :rtype: dict
    """
    reg_leagues = {}

    # Obtain page & soup
    sport_country_url = config.FS_URL + "/" + sport + "/" + country

    soup = rendering.get_soup(sport_country_url)

    reg_leagues_tag = soup.find_all(class_=config.ID_MAIN_REG_LEAGUES)
    reg_league_re = rf"/{sport}/{country}/([^/]+)/"

    # Go through the tag checking the different reg_leagues
    for rl in reg_leagues_tag:
        reg_league_url = rl.get("href")
        # The regular expression allows us to:
        #   1. Filter that is indeed from "sport" and "country" given
        #      as argument
        #   2. Obtain the "keyname"
        match_reg_league = re.match(reg_league_re, reg_league_url)

        if match_reg_league:
            reg_league_keyname = match_reg_league.group(1)
            reg_league_name = rl.get_text(strip=True)
            reg_leagues.update({reg_league_keyname: reg_league_name})

    return reg_leagues


# !TODO: Bug found. If for instance laliga has 22 rounds played. It wont
#        load the 10th round. A further look should be taken here.
#        Maybe it is not displaying everything.
def get_results(sport: str, country: str, league: str, round: int = 0):
    """
    Get function to obtain the results of all the games in a
    specific round.
    """
    games = [ ]

    # URL
    results_url = f"{config.FS_URL}/{sport}/{country}/{league}/results/"

    soup = rendering.get_soup(results_url)

    # Find all the games
    round_tag = soup.find_all(class_=config.ID_ROUND)

    # We obtain the first round (last one that occurred)
    last_round_text = round_tag[0].get_text()
    round_re = r"^Round\s(\d+)$"
    match = re.match(round_re, last_round_text)
    last_round_n = int(match.group(1))

    # We check whether it has happened or not
    desired_round_n = last_round_n - round

    if desired_round_n < 0:
        raise ValueError("Bad Argument Error - [ROUND]. "
                         f"Last round was {last_round_n}")

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
    cmatch = round_tag[desired_round_n].find_next_sibling()

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
    Internal get functionality to obtain a certain team's id

    :param sport: Given sport in which the team is
    :type sport: str
    :param country: Given country in which the team is
    :type country: str
    :param league: Given league in which the team is
    :type league: str
    :param team: Keyname of the team
    :type team: str
    :return: ID of the given's keyname team
    :rtype: str
    """
    team_id = None
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
            team_id = splitted_team_href[3]
            return team_id

    if team_id is None:
        raise ValueError("Bad Argument Error - [TEAM]. "
                        f"No team {team} has been found")


def get_team_squad(sport: str, country: str, league: str,
                    team: str) -> list[containers.Player]:
    """
    Get functionality that allows you to the whole squad from a certain
    team.

    :param sport: Description
    :type sport: str
    :param country: Description
    :type country: str
    :param league: Description
    :type league: str
    :param team: Description
    :type team: str
    :return: Description
    :rtype: list[Player]
    """
    squad = []
    names = []

     # We need the id...
    team_id = get_team_id(sport, country, league, team)

    # To create the url
    squad_url = f"{config.FS_URL}/team/{team}/{team_id}/squad"

    # We extract the rederized HTML
    squad_soup = rendering.get_soup(squad_url)

    # Each row contains a player from the table
    players_tag = squad_soup.find_all(class_=config.CLASS_LU_ROW)

    for player_tag in players_tag:
        name_tag = player_tag.find(class_=config.CLASS_SQ_NAME)
        if name_tag:
            name = name_tag.get_text(strip=True)

        # There are different squads, therefore we check if it has been
        # added before
        if name not in names:
            names.append(name)

            # We reset variables if age or jersey are not found,
            # for instance coaches
            age = None
            jersey = None

            age_tag = player_tag.find(class_=config.CLASS_SQ_AGE)
            if age_tag:
                age = age_tag.get_text(strip=True)

            jersey_tag = player_tag.find(class_=config.CLASS_SQ_NUM)
            if jersey_tag:
                jersey = jersey_tag.get_text(strip=True)

            squad.append(containers.Player(name, age, jersey))

    return squad


def get_team_next_games(sport: str, country: str,
                        league: str, team: str) -> tuple[containers.Match]:
    """
    This get functionality allows you to check the games that are
    registered to occur to a certain team

    :param sport: Desired sport to analyze
    :type sport: str
    :param country: Desired country
    :type country: str
    :param league: Desired league
    :type league: str
    :param team: Desired team from which will be listed the next games
    :type team: str
    :return: List of Matches
    :rtype: tuple[containers.Match]
    """
    next_games = []

    # We need the id...
    team_id = get_team_id(sport, country, league, team)

    # To create the url
    fixtures_url = f"{config.FS_URL}/team/{team}/{team_id}/fixtures"

    # We extract the rederized HTML
    soup = rendering.get_soup(fixtures_url, f".{config.CLASS_SCHEDULED}")

    fixtures_table_tag = soup.find(class_=config.CLASS_LEAGUE)

    league_name = None
    league_url = None

    for fixture_row in fixtures_table_tag.children:
        class_row = fixture_row.get("class")
        # In case it is a header of a league we obtain the current league
        if config.CLASS_LEAGUE_WRAPPER in class_row:
            cleague_tag = fixture_row.find(class_=config.CLASS_HEADER_LEAGUE)
            league_name = cleague_tag.get("title")
            league_url = cleague_tag.get("href")
            league_keyname_re = rf"/{sport}/([^/]+)/([^/]+)/"
            match = re.match(league_keyname_re, league_url)
            region_keyname = match.group(1)
            league_keyname = match.group(2)
        # In case it is an event we fill the Match object, and add the league
        # info that is curret
        elif config.ID_MATCHROW in class_row:
            time_tag = fixture_row.find(class_=config.CLASS_TIME)
            time = time_tag.get_text()
            local_team_tag = fixture_row.find(class_=config.ID_LOCALTEAM)
            local_team = local_team_tag.get_text()
            away_team_tag = fixture_row.find(class_=config.ID_AWAYTEAM)
            away_team = away_team_tag.get_text()

            current_match = containers.Match(time,
                                             [None, local_team], None,
                                             [None, away_team], None,
                                             [league_keyname, league_name],
                                             [None, region_keyname])

            next_games.append(current_match)

    return next_games


# !TODO: Add the Match class to all the times it is used, for instance here
def get_team_prev_games(sport: str, country: str,
                        league: str, team: str) -> tuple[containers.Match]:
    """
    This get functionality allows you to check the games that are
    registered to have occured to a certain team

    :param sport: Desired sport to analyze
    :type sport: str
    :param country: Desired country
    :type country: str
    :param league: Desired league
    :type league: str
    :param team: Desired team from which will be listed the previous games
    :type team: str
    :return: List of Matches
    :rtype: tuple[containers.Match]
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

    # This is the overall section
    league_event_section = soup.find(class_=config.CLASS_LEAGUE_TAG)

    # For each div...
    for row in league_event_section.children:
        class_row = row.get("class")

        # We select if it's either league...
        if config.CLASS_LEAGUE_WRAPPER in class_row:
            cleague_tag = row.find(class_=config.CLASS_HEADER_LEAGUE)
            league_name = cleague_tag.get("title")
            league_url = cleague_tag.get("href")
            league_keyname_re = rf"/{sport}/([^/]+)/([^/]+)/"
            match = re.match(league_keyname_re, league_url)
            region_keyname = match.group(1)
            league_keyname = match.group(2)
        # Or event!
        elif config.ID_MATCHROW in class_row:
            home_team = row.find(class_=config.ID_LOCALTEAM).get_text()
            home_score = row.find(class_=config.ID_LOCALSCORE).get_text()
            away_team = row.find(class_=config.ID_AWAYTEAM).get_text()
            away_score = row.find(class_=config.ID_AWAYSCORE).get_text()
            date = row.find(class_=config.CLASS_TIME).get_text()

            current_match = containers.Match(date,
                                             [None, home_team], home_score,
                                             [None, away_team], away_score,
                                             [league_keyname, league_name],
                                             [None, region_keyname])

            prev_games.append(current_match)


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

    if partial_section_url is None:
        raise ValueError("Bad Argument Error - [SECTION]. "
                         f"No section named {section} was found available")

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
