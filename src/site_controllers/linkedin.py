import os
import time
import logging
from datetime import timedelta
from selenium.webdriver.common.keys import Keys

from site_controllers.controller import Controller
from site_controllers.decorators import *
from emails import PinValidator, PinValidationException

from common.logging import initial_timestamp, LOG_FILES_DIR
from common.stringmanipulations import onlyAplhaNumeric


@log_all_exceptions
class LinkedInController(Controller):
    """
    The controller for LinkedIn
    """

    def __init__(self, *args, **kwargs):
        """Initializes LinkedIn Controller"""

        Controller.__init__(self, *args, **kwargs)
        self._initialURL = 'https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin'
        self.info(f"Creating Linkedin controller for {self._username}")

    def initLogger(self):
        """Creates a logger for this user's linkedin controller only"""
        alphaNumericName = onlyAplhaNumeric(self._username, '_')
        filename = os.path.abspath(os.path.join(LOG_FILES_DIR, f"{initial_timestamp}--{alphaNumericName}.log"))
        format_str = '%(asctime)s - %(levelname)s - %(message)s'
        handler = logging.FileHandler(filename, encoding='UTF-8', delay=True)
        handler.setFormatter(logging.Formatter(format_str))
        self._loggerName = f"controller.linkedin.{alphaNumericName}"
        self._logger = logging.getLogger(self._loggerName)
        self._logger.addHandler(handler)
        self._logger.setLevel(logging.DEBUG)

    @ensureBrowserIsRunning
    def login(self):
        """Logs in to LinkedIn"""

        self.info("Logging in")
        if "Login" in self.browser.title or "Sign in" in self.browser.title:
            self.info(f"Entering email: {self._email}")
            self.browser.find_element_by_id("username").send_keys(self._email)
            self.info(f"Entering password: {'*'*len(self._password)}")
            self.browser.find_element_by_id("password").send_keys(self._password)
            self.info("Submitting login request")
            self.browser.find_element_by_css_selector('button[type=submit]').click()

        if "Security Verification" in self.browser.title:
            self.warning("Detected Security verification page")
            # Determine if it's asking for a pin
            pin_inputs = self.browser.find_elements_by_id("input__email_verification_pin")
            if pin_inputs:
                timeout = timedelta(minutes=15)
                self.info("Detected pin validation method. Retrieving PIN from email.")
                pin = PinValidator().get_pin(self._username, self._email, timeout)
                self.info(f"Retrieved PIN: {pin}")
                pin_inputs[0].send_keys(pin + Keys.RETURN)

            # Determine if it's asking for a recaptcha
            # TODO: Implement

            else:
                self.critical("An unknown security verification technique was detected.")

    @authentication_required
    def searchMessagesFor(self, person: str):
        """Searches messages for the name entered, and gets the first person from the list"""
        self.info(f"Searching for {person} in messages")

        self.info("Finding connection list bar")
        connection_bar = self.browser.find_element_by_css_selector("header[data-control-name$=_connection_list_bar]")
        if "maximize" in connection_bar.get_attribute("data-control-name"):
            self.highlightElement(connection_bar)
            self.info("Connection list is minimized. Opening it now.")
            connection_bar.click()
        else:
            self.info("Connection list is already maximized")

        time.sleep(1)
        self.info("Searching for the search field")
        searchbox = self.browser.find_element_by_id("msg-overlay-list-bubble-search__search-typeahead-input")
        self.highlightElement(searchbox)
        self.info("Clearing the search field")
        searchbox.send_keys(Keys.CONTROL + "a")
        searchbox.send_keys(Keys.DELETE)
        self.info(f"Entering name in search field: {person}")
        searchbox.send_keys(person)
        searchbox.send_keys(Keys.RETURN)
        time.sleep(1)
        self.info(f"Finding link to {person}'s list element")
        concat = "concat(\"" + "\", \"".join(list(person)) + "\")"
        target_account = self.browser.find_element_by_xpath(f"//h4[text()={concat}]/../../..")
        self.highlightElement(target_account)
        self.info("Clicking on connection to open messaging box")
        target_account.click()

    @authentication_required
    def closeAllChatWindows(self):
        """Closes all open chat windows"""
        # I was having trouble iterating over all chat windows and closing them because when one closes, the others
        # become detached or something. Refreshing is a more robust way of closing the windows.
        self.info("Clearing all open message dialogs to avoid mis-identification")
        self.browser.refresh()

    @authentication_required
    def sendMessageTo(self, person: str, message: str):
        """Sends a message to the person."""

        msg_details = f"""Sending message:

        To: {person}
        From: {self._username}
        Content: {message}
        """

        self.info(msg_details)
        self.closeAllChatWindows()
        self.searchMessagesFor(person)

        self.info("Finding the message box")
        msg_box = self.browser.find_element_by_class_name("msg-form__contenteditable")
        self.highlightElement(msg_box)
        self.info(f"Typing the message: {message}")
        msg_box.send_keys(message)
        self.info("Finding the submit button")
        msg_send = self.browser.find_element_by_class_name("msg-form__send-button")
        self.highlightElement(msg_send)
        self.info("Sending the message")
        msg_send.click()
