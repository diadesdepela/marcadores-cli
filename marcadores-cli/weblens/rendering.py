import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from bs4 import BeautifulSoup

class RenderingError(Exception):
    """
    Base RenderingError exception
    """

class PageNotFoundError(RenderingError):
    pass


def get_soup(url: str, wait_selector: str = None, 
             timeout: float = 15, wait: float = 1) -> BeautifulSoup:
    """
    Docstring for get_soup
    
    :param url: Where does your soup wanna come from?
    :type url: str
    :param wait_selector: HTML selector to be waited to load
    :type wait_selector: str
    :param time_out: Maximum time to wait the wait_selector
    :type timeout: float
    :param wait: Plain seconds to wait for loading
    :type wait: float
    :return: Soup of the selected URL
    :rtype: BeautifulSoup
    """
    # HEADLESS Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    # Launch Web browser
    driver = webdriver.Chrome(options=chrome_options)
    # This get function does not return until the page is fully loaded
    driver.get(url)

    # Wait if the CSS element is detected
    if wait_selector:
        try:
            WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector))
        )
        except TimeoutException:
            driver.quit()
            raise TimeoutError("Error TimeOut. Couldn't find specified CSS "
                               f"selector in {url}.")


    # General wait
    time.sleep(wait)

    # We obtain the renderized html
    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, "html.parser")

    # In flashscore page loads and prompts a script to show the error
    tags_404 = soup.find_all("script")

    for tag in tags_404:
        if "404_page" in tag.get_text():
            raise PageNotFoundError(f"Error 404. Page ({url}) not found, "
                                     "try other arguments.")

    return BeautifulSoup(html, "html.parser")
