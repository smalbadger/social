from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import InvalidSelectorException
import time

from data.controllers.controller import Controller
from resources.credentials.linkedin import username, password
from resources.decorators import ensureUserLoggedIn, ensureBrowserIsRunning


class LinkedInController(Controller):
    """
    The controller for LinkedIn
    """

    def __init__(self, browser: str, connections: str, args: list = None):
        """
        Initializes controller

        :param browser: A string describing the browser to use
        :type browser: str
        :param connections: absolute path to connections file
        :type connections: str
        :param args: Arguments to use when launching the browser
        :type args: list
        """

        Controller.__init__(self, browser, args)

        self.initURL = 'https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin'
        self.connections = connections
        self.recipient = 'Samuel Badger'

    def login(self):
        """
        Logs in to LinkedIn
        """

        if "Login" in self.browser.title or "Sign in" in self.browser.title:
            print("Logging In")
            self.browser.find_element_by_id("username").send_keys(username)
            self.browser.find_element_by_id("password").send_keys(password)
            self.browser.find_element_by_css_selector('button[type=submit]').click()

            time.sleep(1)

    @ensureBrowserIsRunning
    @ensureUserLoggedIn
    def searchMessagesFor(self, person: str):
        """
        Searches messages for the name entered, and gets the first person from the list
        """

        try:
            self.browser.find_element_by_css_selector("a[data-control-name=overlay.maximize_connection_list_bar]").click()
        except InvalidSelectorException as e:
            print("Could not find the message-maximize button. We're assuming it's already expanded.")

        searchbox = self.browser.find_element_by_id("msg-overlay-list-bubble-search__search-typeahead-input")
        searchbox.send_keys(person)
        searchbox.send_keys(Keys.RETURN)

        time.sleep(.1)
        # results = self.browser.find_element_by_class_name("msg-overlay-list-bubble-search__search-result-container")
        target_account = self.browser.find_element_by_xpath(f"//h4[text()='{person}']")
        target_account.click()

    @ensureBrowserIsRunning
    @ensureUserLoggedIn
    def sendMessageTo(self, person: str, message: str):
        """
        Sends a message to the person.
        """

        self.searchMessagesFor(person)

        time.sleep(.1)
        msg_box = self.browser.find_element_by_class_name("msg-form__contenteditable")
        msg_box.send_keys(message)
        time.sleep(.5)
        msg_send = self.browser.find_element_by_class_name("msg-form__send-button")
        msg_send.click()
