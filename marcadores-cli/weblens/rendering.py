import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from bs4 import BeautifulSoup


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
    driver.get(url)

    # Wait if the CSS element is detected
    if wait_selector:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector))
        )
    # !TODO: Implement here exception! TimeOut

    # General wait
    time.sleep(wait)

    # We obtain the renderized html
    html = driver.page_source
    driver.quit()

    return BeautifulSoup(html, "html.parser")
