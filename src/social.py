"""
Scrape the LinkedIn conversations
"""
import os
import time

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import InvalidSelectorException

from credentials.linkedin import username, password

if __name__ == "__main__":

    # add the driver to the PATH variable

    os.environ["PATH"] += os.pathsep + os.path.abspath(os.path.join("..", "drivers", "windows"))

    opts = Options()
    #opts.add_argument("--headless")
    #assert opts.headless
    browser = Chrome(options=opts)

    # Just want to put here that I had problems with this at the beginning but they got resolved just by trying a couple
    # of times.
    browser.get('https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin')

    if "Login" in browser.title or "Sign in" in browser.title:
        print("Logging In")
        browser.find_element_by_id("username").send_keys(username)
        browser.find_element_by_id("password").send_keys(password)
        browser.find_element_by_css_selector('button[type=submit]').click()

    time.sleep(1)

    try:
        browser.find_element_by_css_selector("a[data-control-name=overlay.maximize_connection_list_bar]").click()
    except InvalidSelectorException as e:
        print("Could not find the message-maximize button. We're assuming it's already expanded.")

    time.sleep(1)

    # recipient = "Philippe Cutillas"
    recipient = "Samuel Badger"

    searchbox = browser.find_element_by_id("msg-overlay-list-bubble-search__search-typeahead-input")
    searchbox.send_keys(recipient)
    searchbox.send_keys(Keys.RETURN)

    time.sleep(1)
    results = browser.find_element_by_class_name("msg-overlay-list-bubble-search__search-result-container")
    target_account = browser.find_element_by_xpath(f"//h4[text()='{recipient}']")
    target_account.click()

    time.sleep(1)
    msg_box = browser.find_element_by_class_name("msg-form__contenteditable")
    msg_box.send_keys("Yo I got the auto-downloading working, this is an automated message!")
    time.sleep(1)
    msg_send = browser.find_element_by_class_name("msg-form__send-button")
    msg_send.click()

    browser.close()
