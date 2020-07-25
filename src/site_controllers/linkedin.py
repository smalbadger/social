import os
import sys
import html
import logging
from datetime import timedelta, datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException

from site_controllers.controller import Controller
from site_controllers.exceptions import *
from site_controllers.decorators import *
from emails import PinValidator

from common.logging import initial_timestamp, LOG_FILES_DIR
from common.stringmanipulations import onlyAplhaNumeric
from common.waits import random_uniform_wait, send_keys_at_irregular_speed, necessary_wait, TODO_get_rid_of_this_wait


class LinkedInException(ControllerException):
    def __init__(self, msg):
        ControllerException.__init__(self, msg)


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

        format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        noname_format_str = '%(asctime)s - %(levelname)s - %(message)s'

        filehandler = logging.FileHandler(filename, encoding='UTF-8', delay=True)
        filehandler.setFormatter(logging.Formatter(noname_format_str))

        stdout = logging.StreamHandler(sys.stdout)
        stdout.setFormatter(logging.Formatter(format_str))

        self._loggerName = f"controller.linkedin.{alphaNumericName}"
        self._logger = logging.getLogger(self._loggerName)
        self._logger.addHandler(filehandler)
        self._logger.addHandler(stdout)
        self._logger.setLevel(logging.DEBUG)

    def auth_check(self):
        # TODO: Improve this check
        return "Login" not in self.browser.title and "Sign in" not in self.browser.title

    @ensure_browser_is_running
    def login(self, manual=False):
        """
        Logs in to LinkedIn

        TODO: check if we're connected. raise NotConnectedException
        TODO: Check to see if the credentials were valid. Raise AuthenticationException if not
        TODO: Make sure we successfully arrived at the correct webpage after submitting credentials. Raise LinkedInException if no other
        TODO: Detect if the reCAPTCHA called us out for being a bot. raise CaptchaBotDetectedException

        :raises InvalidCredentialsException: If the email/password didn't match
        :raises PinValidationException: If there was a problem retrieving the validation pin.
        :raises SecurityVerificationException: If an unknown security verification method is used or
        :raises CaptchaTimeoutException: If a captcha appears and was not solved in time
        :raises LinkedInException: If we arrived at an unknown location or there was another issue.

        :param manual: If True, wait for the user to click the submit button. Credentials are entered automatically.
        :type manual: bool
        """

        self.info("Logging in")

        # NOTE: If the browser has left LinkedIn for some reason, we return to the initial url
        if "linkedin.com" not in self.browser.current_url:
            self.browser.get(self._initialURL)
            necessary_wait(3)

        # NOTE: I have been logged out automatically by LinkedIn on one of the test accounts and I assume it's because
        #       they detect I'm using automation software. If this happens, we are sent to the login or sign up page.
        #       at which point, we just try to sign in again after a fairly significant wait.
        if self.browser.title == "Linkedin: Log In or Sign Up":
            sign_in_button = self.browser.find_element_by_link_text("Sign in")
            random_uniform_wait(3, 6, self)
            sign_in_button.click()

        # NOTE: Now we're back to the normal sign in page, but if we sign in too fast, LinkedIn will detect that we're a
        #       bot, so we use some randomness to lessen the chances of hitting a reCAPTCHA.
        if "Login" in self.browser.title or "Sign in" in self.browser.title:

            self.info(f"Entering email: {self._email}")
            send_keys_at_irregular_speed(self.browser.find_element_by_id("username"), self._email, 1, 3, 0, .25)
            self.info(f"Entering password: {'*'*len(self._password)}")
            send_keys_at_irregular_speed(self.browser.find_element_by_id("password"), self._password, 1, 3, 0, .25)

            # If manual is True, we require the user to press the login button.
            if manual:
                while not self.browser.current_url == self._initialURL:
                    necessary_wait(.1)
            else:
                self.info("Submitting login request")
                random_uniform_wait(1, 3)
                self.browser.find_element_by_css_selector('button[type=submit]').click()

        # NOTE: At this point, we've signed in, but we might not be done. If LinkedIn has detected your activity as
        #       suspicious, they'll do some types of security verification:
        #
        #       1. They might send an email that contains a pin. We can beat this easily.
        #       2. They might send a recaptcha in which case, we need the user to intervene. In some cases, the recaptcha
        #          doesn't let the user solve it because it determines that the user is using automation software 100%.
        if "Security Verification" in self.browser.title:
            self.warning("Detected Security verification page")
            method = ""

            # Determine if it's asking for a pin
            pin_inputs = self.browser.find_elements_by_id("input__email_verification_pin")
            if pin_inputs:
                method = "pin"
                timeout = timedelta(minutes=1)
                self.info("Detected pin validation method. Retrieving PIN from email.")
                pin = PinValidator().get_pin(self._username, self._email, timeout)
                self.info(f"Retrieved PIN: {pin}")
                pin_inputs[0].send_keys(pin + Keys.RETURN)
                return

            # Determine if it's asking for a recaptcha
            timeout = timedelta(minutes=5)
            found = False
            while True:
                captcha = self.browser.find_elements_by_id('captcha-challenge')
                if captcha:
                    if not found:
                        self.critical(f"Detected Captcha. You have {timeout.total_seconds()/60} minutes to solve it.")
                        method = "captcha"
                        start = datetime.now()
                        found = True

                if not found:
                    self.info("Captcha was not detected.")
                    break
                elif found and not captcha:
                    self.info("Captcha solved.")
                    break
                elif datetime.now() - start > timeout:
                    raise CaptchaTimeoutException("Captcha timed out.")

            if not method:
                raise SecurityVerificationException("An unknown security verification technique was detected.")

    @authentication_required
    def maximizeConnectionPopup(self):
        """opens the connection popup"""
        self.info("Finding connection list bar")
        cbt = "header[data-control-name={}imize_connection_list_bar]"  # connection bar template
        possible_connection_bars = self.browser.find_elements_by_class_name("msg-overlay-bubble-header")
        for possibility in possible_connection_bars:
            if possibility.get_attribute("data-control-name") == "overlay.maximize_connection_list_bar":
                self.info("maximizing the connection list")
                possibility.click()

    @authentication_required
    def searchForConnectionInPopup(self, person: str):
        """Only search for a person in the popup connections bar."""
        self.info(f"Searching for {person} in messages")

        # make sure conversation list is visible
        searchbox = WebDriverWait(self.browser, 3).until(
            EC.visibility_of_element_located((By.ID, "msg-overlay-list-bubble-search__search-typeahead-input")))
        self.info("The search field has been found")
        self.highlightElement(searchbox)
        self.info("Clearing the search field")
        searchbox.send_keys(Keys.CONTROL + "a")
        searchbox.send_keys(Keys.DELETE)
        self.info(f"Entering name in search field: {person}")
        searchbox.send_keys(person)
        searchbox.send_keys(Keys.RETURN)

    @authentication_required
    def selectConnectionFromPopup(self, person: str):
        """Select a person from the popup connection bar assuming they're already shown."""
        self.info(f"Finding link to {person}'s list element")
        concat = "concat(\"" + "\", \"".join(list(person)) + "\")"
        necessary_wait(1)
        target_account = WebDriverWait(self.browser, 10) \
            .until(EC.element_to_be_clickable((By.XPATH, f"//h4[text()={concat}]/../..")))
        self.info(f"scrolling through results to {person}")
        ActionChains(self.browser).move_to_element(target_account).perform()
        self.highlightElement(target_account)
        self.info("Clicking on connection to open messaging box")
        target_account.click()

    @authentication_required
    def openConversationWith(self, person: str):
        """Searches messages for the name entered, and gets the first person from the list"""
        self.searchForConnectionInPopup(person)
        self.selectConnectionFromPopup(person)

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
        self.openConversationWith(person)

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

    @authentication_required
    def acceptAllConnections(self) -> list:
        """Accepts all connections and returns them as a list of (name, profileLink) tuples"""

        accepted = []

        self.info("Switching to network page")
        self.browser.get('https://www.linkedin.com/mynetwork/')

        self.info('Getting connection requests')
        try:
            acceptButtons = self.browser.find_elements_by_xpath(
                "//button[@class='invitation-card__action-btn artdeco-button artdeco-button--2 "
                "artdeco-button--secondary ember-view']"
            )

            if not acceptButtons:
                raise NoSuchElementException

        except NoSuchElementException:
            self.info("No connections to accept, exiting with empty list.")
            return accepted

        for button in acceptButtons:
            # Split at ’ to cut off tail. Then recombine with it if it's a list, which means there was a ’ in the name.
            # Then cut off "Accept " from beginning, and convert from HTML for special character handling
            tmp = button.get_attribute('aria-label').split("’")[:-2]
            if len(tmp) > 1:
                tmp = "’".join(tmp)
            else:
                tmp = tmp[0]

            connectionName = html.unescape(tmp[len('Accept '):])
            firstName = connectionName.split(' ')[0]

            self.info(f"Accepting {firstName} and adding to new connections list")
            profLinkElement = self.browser.find_element_by_xpath(f'//span[text()="{connectionName}"]').find_element_by_xpath("./..")
            profLink = profLinkElement.get_attribute('href')
            button.click()

            accepted.append((connectionName, profLink))

        return accepted
