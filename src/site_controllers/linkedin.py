import os
import time
import logging
from datetime import timedelta
from selenium.webdriver.common.keys import Keys

from site_controllers.controller import Controller
from site_controllers.decorators import authentication_required, ensureBrowserIsRunning, print_page_on_exception
from emails import PinValidator, PinValidationException

from common.logging import initial_timestamp, LOG_FILES_DIR
from common.stringmanipulations import onlyAplhaNumeric


class LinkedInController(Controller):
    """
    The controller for LinkedIn
    """

    def __init__(self, *args, **kwargs):
        """Initializes LinkedIn Controller"""

        Controller.__init__(self, *args, **kwargs)
        self._initialURL = 'https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin'
        self._logger.info(f"Creating Linkedin controller for {self._username}")

    def initLogger(self):
        """Creates a logger for this user's linkedin controller only"""
        alphaNumericName = onlyAplhaNumeric(self._username, '_')
        filename = os.path.abspath(os.path.join(LOG_FILES_DIR, f"{initial_timestamp}--{alphaNumericName}.log"))
        format_str = '%(asctime)s - %(levelname)s - %(message)s'
        handler = logging.FileHandler(filename, encoding='unicode_escape', delay=True)
        handler.setFormatter(logging.Formatter(format_str))
        self._loggerName = f"controller.linkedin.{alphaNumericName}"
        self._logger = logging.getLogger(self._loggerName)
        self._logger.addHandler(handler)
        self._logger.setLevel(logging.DEBUG)

    @ensureBrowserIsRunning
    def login(self):
        """Logs in to LinkedIn"""

        self._logger.info("Logging in")
        if "Login" in self.browser.title or "Sign in" in self.browser.title:
            self._logger.debug("Entering username")
            self.browser.find_element_by_id("username").send_keys(self._email)
            self._logger.debug("Entering password")
            self.browser.find_element_by_id("password").send_keys(self._password)
            self._logger.debug("Submitting login request")
            self.browser.find_element_by_css_selector('button[type=submit]').click()

        if "Security Verification" in self.browser.title:
            self._logger.warning("Detected Security verification page")
            # Determine if it's asking for a pin
            pin_inputs = self.browser.find_elements_by_id("input__email_verification_pin")
            if pin_inputs:
                timeout = timedelta(minutes=15)
                self._logger.info("Detected pin validation method. Retrieving PIN from email.")
                pin = PinValidator().get_pin(self._username, self._email, timeout)
                if pin:
                    self._logger.info(f"Retrieved PIN: {pin}")
                    pin_inputs[0].send_keys(pin + Keys.RETURN)
                else:
                    raise VerificationException("Fatal: Unable to detect PIN")

            else:
                self._logger.critical("An unknown security verification technique was detected.")
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
