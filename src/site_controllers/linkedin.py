from selenium.webdriver.common.keys import Keys
import time
from datetime import timedelta

from site_controllers.controller import Controller
from site_controllers.decorators import authentication_required, ensureBrowserIsRunning, print_page_on_exception
from emails import PinValidation
from common import logging
from common.stringmanipulations import onlyAplhaNumeric


class LinkedInController(Controller):
    """
    The controller for LinkedIn
    """

    def __init__(self, *args, **kwargs):
        """Initializes LinkedIn Controller"""

        Controller.__init__(self, *args, **kwargs)
        self._initialURL = 'https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin'
        self._logger = logging.getLogger(f"controller.linkedin.{onlyAplhaNumeric(self._username, '_')}")

    @ensureBrowserIsRunning
    def login(self):
        """Logs in to LinkedIn"""

        if "Login" in self.browser.title or "Sign in" in self.browser.title:
            self.browser.find_element_by_id("username").send_keys(self._email)
            self.browser.find_element_by_id("password").send_keys(self._password)
            self.browser.find_element_by_css_selector('button[type=submit]').click()

        if "Security Verification" in self.browser.title:

            # Determine if it's asking for a pin
            pin_inputs = self.browser.find_elements_by_id("input__email_verification_pin")
            if pin_inputs:
                timeout = timedelta(minutes=15)
                pin = PinValidation().get_pin(self._username, self._email, timeout)
                pin_inputs[0].send_keys(pin + Keys.RETURN)

            # Determine if it's asking for a recaptcha
            # TODO: Implement

    @authentication_required
    def searchMessagesFor(self, person: str):
        """Searches messages for the name entered, and gets the first person from the list"""

        connection_bar = self.browser.find_element_by_css_selector("header[data-control-name$=_connection_list_bar]")
        if "maximize" in connection_bar.get_attribute("data-control-name"):
            self.highlightElement(connection_bar)
            connection_bar.click()

        searchbox = self.browser.find_element_by_id("msg-overlay-list-bubble-search__search-typeahead-input")
        self.highlightElement(searchbox)
        searchbox.send_keys(Keys.CONTROL + "a")
        searchbox.send_keys(Keys.DELETE)
        searchbox.send_keys(person)
        searchbox.send_keys(Keys.RETURN)

        time.sleep(1) # CAUTION!

        concat = "concat(\"" + "\", \"".join(list(person)) + "\")"
        target_account = self.browser.find_element_by_xpath(f"//h4[text()={concat}]/../../..")
        self.highlightElement(target_account)
        target_account.click()

    @authentication_required
    def closeAllChatWindows(self):
        """Closes all open chat windows"""
        # I was having trouble iterating over all chat windows and closing them because when one closes, the others
        # become detached or something. Refreshing is a more robust way of closing the windows.
        self.browser.refresh()
        time.sleep(1)

    @authentication_required
    @print_page_on_exception
    def sendMessageTo(self, person: str, message: str):
        """Sends a message to the person."""

        self.closeAllChatWindows()
        self.searchMessagesFor(person)

        msg_box = self.browser.find_element_by_class_name("msg-form__contenteditable")
        self.highlightElement(msg_box)
        msg_box.send_keys(message)
        time.sleep(1) # CAUTION!
        msg_send = self.browser.find_element_by_class_name("msg-form__send-button")
        self.highlightElement(msg_send)
        msg_send.click()
