# 
# filename:     spyglass.py
# description:  contains all the necessary functions to access
#               the scoreboard
#

import requests
from bs4 import BeautifulSoup

from config import FS_URL, ID_MAIN_SPORTS

def get_sports_list() -> list[str]:
    """
    Looks for the available sports in the webpage, using the class
    identifier from the HTML file
    """
    sports = []

    # Obtain page & soup
    main_page = requests.get(FS_URL)
    soup = BeautifulSoup(main_page.content, "html.parser")

    # Obtain all the main sports via the class identifier
    main_sports_tag = soup.find_all(class_=ID_MAIN_SPORTS)

    # Fill our list
    for tag in main_sports_tag:
        sports.append(tag.get_text(strip=True))

    #!TODO: Add the secondary sports, create special case for
    #       'Favourites'

    return sports




