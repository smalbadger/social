from selenium.webdriver.common.keys import Keys
import time
from datetime import timedelta

from site_controllers.controller import Controller
from site_controllers.decorators import authentication_required, ensureBrowserIsRunning
from emails import PinValidation

class LinkedInController(Controller):
    """
    The controller for LinkedIn
    """

    def __init__(self, *args, **kwargs):
        """Initializes LinkedIn Controller"""

        Controller.__init__(self, *args, **kwargs)
        self._initialURL = 'https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin'

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
            connection_bar.click()

        searchbox = self.browser.find_element_by_id("msg-overlay-list-bubble-search__search-typeahead-input")
        searchbox.send_keys(Keys.CONTROL + "a")
        searchbox.send_keys(Keys.DELETE)
        searchbox.send_keys(person)
        searchbox.send_keys(Keys.RETURN)

        time.sleep(1) # CAUTION!

        concat = "concat(\"" + "\", \"".join(list(person)) + "\")"
        target_account = self.browser.find_element_by_xpath(f"//h4[text()={concat}]/../../../../../..")
        target_account.click()

    @authentication_required
    def sendMessageTo(self, person: str, message: str):
        """Sends a message to the person."""

        self.searchMessagesFor(person)

        msg_box = self.browser.find_element_by_class_name("msg-form__contenteditable")
        msg_box.send_keys(message)
        time.sleep(1) # CAUTION!
        msg_send = self.browser.find_element_by_class_name("msg-form__send-button")
        msg_send.click()

        time.sleep(1) # CAUTION!
        close_button = self.browser.find_element_by_css_selector("aside#msg-overlay button:nth-child(3)")
        close_button.click()
