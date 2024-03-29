import os
import sys
import html
import logging
from datetime import timedelta, datetime
from dateutil.parser import parse

from PySide2.QtCore import Signal, QThreadPool, QThread, QRunnable

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from site_controllers.controller import Controller, Task
from site_controllers.exceptions import *
from site_controllers.decorators import *
from emails import PinValidator

from common.logging import initial_timestamp, LOG_FILES_DIR
from common.strings import onlyAplhaNumeric, equalTo, fromHTML, xpathConcat
from common.datetime import convertToDate, convertToTime, combineDateAndTime
from common.waits import random_uniform_wait, send_keys_at_irregular_speed, necessary_wait
from common.beacon import Beacon
from common.threading import Task as ncTask

from database.general import Session
from database.linkedin import (LinkedInMessage, LinkedInConnection, LinkedInMessageTemplate,
                               LinkedInAccountDailyActivity, LinkedInAccount)


#########################################################
# Element Identification Strings
#########################################################
class EIS:

    login_header                             = "header__content__heading"  # class
    login_email_input                        = "username"  # id
    login_password_input                     = "password"  # id
    login_submit_button                      = "button[type=submit]"  # css selector

    captcha_challenge                        = "captcha-challenge"  # id
    pin_verification_input                   = "input__email_verification_pin"  # id

    general_search_bar                       = '//input[@placeholder="Search"]'  # xpath

    popup_connection_bar                     = "msg-overlay-bubble-header"  # class
    popup_connection_bar_maximize            = "overlay.maximize_connection_list_bar"  # data-control-name css selector
    popup_connection_search                  = "msg-overlay-list-bubble-search__search-typeahead-input"  # id
    popup_connection_message_select          = "//h4[text()={search}]/../.."  # xpath (must be formatted)
    popup_connection_messaging_popup_close   = '//header/section/button/li-icon[@type="cancel-icon"]/..'  # xpath

    my_network_connection_search             = "mn-connections-search-input" # id
    my_network_connection_message_button     = "//button[@aria-label={search}]" #xpath (must be formatted)

    message_scroll_box                       = "msg-s-message-list"  # class
    message_editor                           = "msg-form__contenteditable"  # class
    message_send                             = "msg-form__send-button"  # class
    message_item                             = "msg-s-message-list__event"  # class
    message_date                             = "msg-s-message-list__time-heading"  # class
    message_time                             = "msg-s-message-group__timestamp"  # class
    message_author                           = "msg-s-message-group__name"  # class
    message_body                             = "msg-s-event-listitem__body"  # class

    profile_link                             = '//span[text()="{connectionName}"]./..'  # xpath (must be formatted)
    connection_request_accept_button         = "//button[@class='invitation-card__action-btn artdeco-button" \
                                               "artdeco-button--2 artdeco-button--secondary ember-view']"  # xpath

    profile_picture                          = '//div[@data-control-name="identity_profile_photo"]/..'  # xpath
    all_connections_link                     = '//a[@data-control-name="topcard_view_all_connections"]'  # xpath
    connection_card                          = 'search-result__wrapper'  # class
    connection_card_info_class               = 'search-result__info'  # class
    connection_card_profile_link             = '[data-control-name="search_srp_result"]'  # css selector
    connection_card_position                 = "subline-level-1"  # class
    connection_card_location                 = "subline-level-2"  # class
    connection_card_mutual_text              = 'search-result__social-proof-count'
    connection_card_mutual_link              = '[data-control-name="view_mutual_connections"]'  # css selector
    no_results_button                        = '//button[@data-test="no-results-cta"]'  # xpath
    connect_button                           = 'button[data-control-name="srp_profile_actions"]'  # css selector
    confirm_request_button                   = '//button[@aria-label="Send now"]'

    all_filters_button                       = '//button[@data-control-name="all_filters"]'  # xpath
    apply_all_filters_button                 = '//button[@data-control-name="all_filters_apply"]'  # xpath
    first_connections_box                    = 'sf-network-F'  # id
    second_connections_box                   = 'sf-network-S'  # id
    location_box                             = '//input[@placeholder="Add a country/region"]'  # xpath
    current_company_box                      = '//input[@placeholder="Add a current company"]'  # xpath
    firstname_box                            = 'search-advanced-firstName'  # id
    lastname_box                             = 'search-advanced-lastName'  # id


class LinkedInException(ControllerException):
    def __init__(self, msg):
        ControllerException.__init__(self, msg)


class LinkedInController(Controller):
    """
    The controller for LinkedIn
    """

    Beacon.connectionsScraped = Signal()
    Beacon.messageSent = Signal(int, int)  # connection id, message id
    Beacon.requestSent = Signal()

    CRITICAL_LOGIN_INFO = ("email", "password")

    @log_exceptions
    def __init__(self, *args, **kwargs):
        """Initializes LinkedIn Controller"""

        Controller.__init__(self, *args, **kwargs)
        self._initialURL = 'https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin'
        self.mainWindow = None
        self.mutualWindow = None
        self._criticalLoginInfo = LinkedInController.CRITICAL_LOGIN_INFO
        self.checkForValidConfiguration()
        self.debug(f"Created LinkedIn controller for {self._profile_name}")
        self.setMessageDelayRange(1, 2)

    @log_exceptions
    def initLogger(self):
        """Creates a logger for this user's linkedin controller only"""
        alphaNumericName = onlyAplhaNumeric(self._profile_name, '_')
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

    @log_exceptions
    def getLoggerName(self):
        """Gets the name of the logger that this controller is using"""
        return self._loggerName

    @only_if_browser_is_running
    @connection_required
    @log_exceptions
    def auth_check(self):
        # TODO: Improve this check
        return "Login" not in self.browser.title and "Sign in" not in self.browser.title

    @only_if_browser_is_running
    @connection_required
    @finish_executing
    @log_exceptions
    def login(self, manual=False):
        """
        Logs in to LinkedIn

        TODO: check if we're connected. raise NotConnectedException
        TODO: Make sure we successfully arrived at the correct webpage after submitting credentials. Raise AuthenticationException
        TODO: Detect if the reCAPTCHA called us out for being a bot. raise CaptchaBotDetectedException

        :raises InvalidCredentialsException: If the email/password didn't match
        :raises PinValidationException: If there was a problem retrieving the validation pin.
        :raises SecurityVerificationException: If an unknown security verification method is used or
        :raises CaptchaTimeoutException: If a captcha appears and was not solved in time
        :raises AuthenticationException: If we were unable to leave the login page for an unknown reason
        :raises LinkedInException: If we arrived at an unknown location or there was another issue.

        :param manual: If True, wait for the user to click the submit button. Credentials are entered automatically.
        :type manual: bool
        """

        if self.closing:
            QThread.currentThread().terminate()

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

            if self._email:
                self.debug(f"Entering email: {self._email}")
                send_keys_at_irregular_speed(self.browser.find_element_by_id(EIS.login_email_input), self._email, 1, 3, 0, .25)

            if self._password:
                self.debug(f"Entering password: {'*'*len(self._password)}")
                send_keys_at_irregular_speed(self.browser.find_element_by_id(EIS.login_password_input), self._password, 1, 3, 0, .25)

            # If manual is True, we require the user to press the login button (allowing them to change the credentials too)
            if manual:
                self.warning(f"Waiting for credentials to be entered manually for {self._profile_name}")
                header = self.browser.find_element_by_class_name(EIS.login_header)
                self.setInnerText(header, f"Please login for {self._profile_name}")
                while not self.auth_check():
                    necessary_wait(1)
                self.warning(f"Not waiting anymore")
            else:
                self.info("Submitting login request")
                random_uniform_wait(1, 3)
                self.browser.find_element_by_css_selector(EIS.login_submit_button).click()

            if not self.auth_check():
                raise InvalidCredentialsException("Authentication Failed")

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
            pin_inputs = self.browser.find_elements_by_id(EIS.pin_verification_input)
            if pin_inputs:
                entered = False

                def enterPIN(pin):
                    nonlocal entered
                    self.debug(f"Retrieved PIN: {pin}")
                    pin_inputs[0].send_keys(pin + Keys.RETURN)
                    entered = True

                timeout = timedelta(minutes=15)
                self.info("Detected pin validation method. Attempting to retrieve PIN from email.")

                task = ncTask(lambda: PinValidator().get_pin(self._profile_name, self._email, timeout))
                task.finished.connect(enterPIN)
                QThreadPool.globalInstance().start(task)

                start = datetime.now()
                while True:
                    pin_inputs = self.browser.find_elements_by_id(EIS.pin_verification_input)
                    if not pin_inputs and not entered:
                        self.warning('detected that PIN was entered manually.')
                        break
                    elif entered:  # Entered automatically
                        break
                    elif datetime.now() - start > timeout:
                        raise PINTimeoutException("PIN entering timed out.")
                return

            # Determine if it's asking for a recaptcha
            timeout = timedelta(minutes=5)
            found = False
            while True:
                captcha = self.browser.find_elements_by_id(EIS.captcha_challenge)
                if captcha:
                    if not found:
                        self.warning(f"Detected Captcha. You have {timeout.total_seconds()/60} minutes to solve it.")
                        method = "captcha"
                        start = datetime.now()
                        found = True

                if not found:
                    self.debug("Captcha was not detected.")
                    break
                elif found and not captcha:
                    self.info("Captcha solved.")
                    break
                elif datetime.now() - start > timeout:
                    raise CaptchaTimeoutException("Captcha timed out.")

            if not method:
                raise SecurityVerificationException("An unknown security verification technique was detected.")

        if not self.auth_check():
            raise AuthenticationException("For some reason, we couldn't leave the login page.")

    @only_if_browser_is_running
    @connection_required
    @log_exceptions
    @authentication_required
    def maximizeConnectionPopup(self):
        """opens the connection popup"""
        self.debug("Finding connection list bar")
        possible_connection_bars = self.browser.find_elements_by_class_name(EIS.popup_connection_bar)
        for possibility in possible_connection_bars:
            if possibility.get_attribute("data-control-name") == EIS.popup_connection_bar_maximize:
                self.debug("maximizing the connection list")
                possibility.click()

    @only_if_browser_is_running
    @connection_required
    @log_exceptions
    @authentication_required
    def searchForConnection(self, person: str, where:str="POPUP"):
        """
        Search for a person in the popup connections bar.
        :param person: the person to search for
        :param where: "POPUP", "MY_NETWORK", ...
        """
        self.debug(f"Searching for {person}.")

        if where == "MY_NETWORK":
            self.browser.get("https://www.linkedin.com/mynetwork/invite-connect/connections/")
            searchbox_id = EIS.my_network_connection_search
        elif where == "POPUP":
            searchbox_id = EIS.popup_connection_search
        else:
            raise Exception("Invalid search location 'where'")

        # make sure conversation list is visible
        searchbox = WebDriverWait(self.browser, 10).until(
            EC.visibility_of_element_located((By.ID, searchbox_id)))
        self.debug("The search field has been found")
        self.highlightElement(searchbox)
        self.debug("Clearing the search field")
        searchbox.send_keys(Keys.CONTROL + "a")
        searchbox.send_keys(Keys.DELETE)
        self.debug(f"Entering name in search field: {person}")
        send_keys_at_irregular_speed(searchbox, person, 1, 3, 0, .25)
        searchbox.send_keys(Keys.RETURN)

    @only_if_browser_is_running
    @connection_required
    @log_exceptions
    @authentication_required
    def selectConnection(self, person: str, where:str= "POPUP"):
        """
        Select a person to send a message to.
        :param person: The person to search for
        :param where: "POPUP", "MY_NETWORK"
        :return: True if connection was successfully selected and False otherwise
        """
        self.debug(f"Finding link to {person}'s list element")

        # If the person's name has quotations (single or double), use the opposite one to do the XPath search
        q = "'" if '"' in person else '"'

        # Construct the XPath queries depending on where we're searching.
        attempts = []
        if where == "POPUP":
            attempts = [
                EIS.popup_connection_message_select.format(search=q + person + q),
                EIS.popup_connection_message_select.format(search=xpathConcat(person, q))
            ]

        elif where == "MY_NETWORK":
            aria_label = f"Send message to {person}"
            attempts = [
                EIS.my_network_connection_message_button.format(search=q + aria_label + q),
                EIS.my_network_connection_message_button.format(search=xpathConcat(aria_label, q))
            ]

        else:
            raise Exception("Invalid search location 'where'")

        target_account = None
        for xpath_str in attempts:
            necessary_wait(2)
            try:
                target_account = WebDriverWait(self.browser, 3) \
                    .until(EC.element_to_be_clickable((By.XPATH, xpath_str)))
            except TimeoutException:
                self.debug(f"Unable to locate the user in the connections list using the XPath: {xpath_str}")
            else:
                break

        if not target_account:
            return False

        self.debug(f"scrolling through results to {person}")
        ActionChains(self.browser).move_to_element(target_account).perform()
        necessary_wait(1)
        self.highlightElement(target_account)
        self.debug("Clicking on connection to open messaging box")
        target_account.click()
        return True

    @only_if_browser_is_running
    @connection_required
    @log_exceptions
    @authentication_required
    def openConversationWith(self, person: str):
        """Searches messages for the name entered, and gets the first person from the list"""
        self.maximizeConnectionPopup()

        for location in ["POPUP", "MY_NETWORK"]:
            self.searchForConnection(person, where=location)
            conversationOpened = self.selectConnection(person, where=location)
            if conversationOpened:
                return True

        self.error(f"Unable to find connection: {person}.")
        return False

    @only_if_browser_is_running
    @connection_required
    @log_exceptions
    @authentication_required
    def closeAllChatWindows(self):
        """Closes all open chat windows"""
        # I was having trouble iterating over all chat windows and closing them because when one closes, the others
        # become detached or something. Refreshing is a more robust way of closing the windows.
        self.debug("Clearing all open message dialogs to avoid mis-identification")

        while True:
            try:
                target_close_btn = WebDriverWait(self.browser, 1) \
                    .until(EC.element_to_be_clickable((By.XPATH, EIS.popup_connection_messaging_popup_close)))
                target_close_btn.click()
            except:
                break

    def setMessageDelayRange(self, minimum, maximum):
        """Sets the upper and lower bounds (in seconds) for the random delay between messages."""
        self.minMessagingDelay = minimum
        self.maxMessagingDelay = maximum

    @only_if_browser_is_running
    @connection_required
    @finish_executing
    @log_exceptions
    @authentication_required
    def sendMessageTo(self, connection: LinkedInConnection, message: str, template):
        """Sends a message to the person."""
        person = connection.name

        msg_details = f"""Preparing to send message:

                To: {person}
                From: {self._profile_name}
                Content: {message}
                """

        self.info(msg_details)

        if connection.account.dailyActivityLimitReached():
            self.critical(f"Daily activity limit reached! The above message was not sent.")
            return

        self.closeAllChatWindows()
        foundInList = self.openConversationWith(person)
        if not foundInList:
            return False

        self.debug("Finding the message box")
        msg_box = self.browser.find_element_by_class_name(EIS.message_editor)
        self.highlightElement(msg_box)
        self.debug(f"Typing the message: {message}")
        send_keys_at_irregular_speed(msg_box, message, 1, 3, 0, .25)
        self.debug("Finding the submit button")
        msg_send = self.browser.find_element_by_class_name(EIS.message_send)
        self.highlightElement(msg_send)
        self.debug("Sending the message")
        msg_send.click()

        necessary_wait(2) # Wait for the message to be sent

        self.debug("Verifying the message was sent")
        now = datetime.now()
        msg, timestamp = self.getLastMessageWithConnection(person, assumeConversationIsOpened=True)
        if not msg or not equalTo(msg, message, normalize_whitespace=True) or timestamp - now > timedelta(minutes=1):
            self.debug(f"The last message was '{msg}' and it was sent at {timestamp}")
            raise MessageNotSentException(f"The message '{message}' was not sent to {person}")

        self.info("Message Sent!")
        self.debug("Updating database")
        msg = template.createMessageTo(connection)
        msg.recordAsDelivered()
        self.messageSent.emit(connection.id, msg.id)
        Session.add(msg)
        Session.commit()
        return True

    @only_if_browser_is_running
    @connection_required
    @log_exceptions
    @authentication_required
    def messageAll(self, connections: list, usingTemplate, checkPastMessages=True):
        """Messages all connections with the template usingTemplate (a query object)"""

        for connection in connections:  # each connection is a query object

            if not self.isRunning:
                return

            if connection.account.dailyActivityLimitReached():
                self.critical("Daily limit reached. No more messages will be sent on this account")
                return

            # Checking database to see if template was already sent to user
            if checkPastMessages:
                previouslySentMessages = Session.query(LinkedInMessage).filter(
                    LinkedInMessage.recipient_connection_id == connection.id,
                    LinkedInMessage.template_id == usingTemplate.id
                )
                alreadySent = previouslySentMessages.count()

                # For templates pulled from the Legacy database, we need to scrape previous messages
                if not alreadySent and usingTemplate.crc != LinkedInMessageTemplate.defaultCRC:
                    for date, name, msg in self.getConversationHistory(connection.name):
                        if str(usingTemplate.crc) in msg:
                            alreadySent = 1

                            # While we're at it, we create a message and put it in the database so we don't have to scrape
                            # for this combination of template and connection again.
                            msg = LinkedInMessage(template_id=usingTemplate.id, recipient_connection_id=connection.id)
                            Session.add(msg)
                            Session.commit()
                            break

            else:
                alreadySent = 0

            if alreadySent:
                self.warning(f"Skipping {connection.name} because the message has already been sent to them.")
            elif not usingTemplate.isValid(connection):
                self.warning(f"Skipping {connection.name} because the message template was invalid for this connection.")
            else:
                msg = usingTemplate.fill(connection)
                success = self.sendMessageTo(connection, msg, usingTemplate)
                if success:
                    self.debug(f"WAITING BOUNDS: {self.minMessagingDelay} {self.maxMessagingDelay}")
                    random_uniform_wait(self.minMessagingDelay, self.maxMessagingDelay, self)

    @only_if_browser_is_running
    @connection_required
    @log_exceptions
    @authentication_required
    def getLastMessageWithConnection(self, person, assumeConversationIsOpened=False):
        """Gets the last message sent to a specific person"""

        msg = None
        time = None
        date = None
        datetime = None

        necessary_wait(.5)

        messages = self.browser.find_elements_by_class_name(EIS.message_body)
        if messages:
            msg = self.getInnerHTML(messages[-1])

        dates = self.browser.find_elements_by_class_name(EIS.message_date)
        if dates:
            date = convertToDate(self.getInnerHTML(dates[-1]))

        times = self.browser.find_elements_by_class_name(EIS.message_time)
        if times:
            time = convertToTime(self.getInnerHTML(times[-1]))

        if date and time:
            datetime = combineDateAndTime(date, time)

        return msg, datetime

    @only_if_browser_is_running
    @connection_required
    @log_exceptions
    @authentication_required
    def getConversationHistory(self, person: str, numMessages = 1_000_000, assumeConversationIsOpened=False):
        """
        Fetches the conversation history with one person

        :param person: The person to get message history with.
        :param numMessages: The maximum number of messages desired.
        :param closeWindows: Closes all chat windows if True
        :returns: Up to numMessages from the conversation
        :rtype: list of tuples where each element is (datetime, name, msg)
        """

        self.debug(f"Fetching conversation history with {person}")
        if not assumeConversationIsOpened:
            self.closeAllChatWindows()
            self.openConversationWith(person)

        prevHTML = ""
        necessary_wait(1)
        for i in range(round(numMessages / 20)):
            scroll_areas = self.browser.find_elements_by_class_name(EIS.message_scroll_box)
            if scroll_areas:
                scroll_area = scroll_areas[0]
                self.debug(f"Loading previous messages with {person}...")
                self.browser.execute_script("arguments[0].scrollTop = 0;", scroll_area)
                necessary_wait(1)
                currentHTML = scroll_area.get_attribute("innerHTML")
                if currentHTML == prevHTML:
                    break
                else:
                    prevHTML = currentHTML

        messageList = self.browser.find_elements_by_class_name(EIS.message_item)

        search_criteria = {
            "date": EIS.message_date,
            "time": EIS.message_time,
            "name": EIS.message_author,
            "body": EIS.message_body
        }

        self.info(f"Scraping messages with {person}...")
        current = {}
        history = []
        self.browser.implicitly_wait(0)
        for msg in messageList:

            for elem_type, cls in search_criteria.items():
                elements = msg.find_elements_by_class_name(cls)
                for element in elements:
                    current[elem_type] = self.getInnerHTML(element)

                    if elem_type == "date":
                        current[elem_type] = convertToDate(current[elem_type])

                    elif elem_type == "time":
                        current[elem_type] = convertToTime(current[elem_type])

                    elif elem_type == "body":
                        t = combineDateAndTime(current['date'], current.get("time", None))
                        new_msg_body = (t, current["name"], current["body"])
                        history.append(new_msg_body)

        self.browser.implicitly_wait(Controller.IMPLICIT_WAIT)

        self.debug(f"{len(history)} messages with {person} found - returning {min(len(history), numMessages)}")
        wanted_history = history[-numMessages:]
        return wanted_history

    @only_if_browser_is_running
    @connection_required
    @log_exceptions
    @authentication_required
    def acceptAllConnections(self) -> list:
        """Accepts all connections and returns them as a list of (name, profileLink) tuples"""

        accepted = []

        self.debug("Switching to network page")
        self.browser.get('https://www.linkedin.com/mynetwork/')

        self.info('Getting connection requests')
        try:
            acceptButtons = self.browser.find_elements_by_xpath(EIS.connection_request_accept_button)

            if not acceptButtons:
                raise NoSuchElementException

        except NoSuchElementException:
            self.warning("No connections to accept, exiting with empty list.")
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

            self.info(f"Accepting connection request from {firstName}")
            profLinkElement = self.browser.find_element_by_xpath(EIS.profile_link.format(connectionName = connectionName))
            profLink = profLinkElement.get_attribute('href')
            button.click()
            accepted.append((connectionName, profLink))

        return accepted

    @only_if_browser_is_running
    @connection_required
    @log_exceptions
    @authentication_required
    def getNewConnections(self, account_id, known: list = None, getMutualInfoFor: list = None,
                          withLocation=True, withPosition=True, updateConnections=None) -> dict:
        """
        Gets all contacts and returns them in a dictionary
        :param account_id: The account id
        :param known: A list of the currently stored connections' names
        :param getMutualInfoFor: A list of connections you want the mutual connections info for
        :param withLocation: whether to store location information about the connections
        :param withPosition: whether to store job/position info about the connections
        :param updateConnections: update all info for those in this list
        """

        self.info('Getting all connections')

        self.browser.get('https://www.linkedin.com/in/me/')

        # Find connection page link, click on it
        connLink = self.browser.find_element_by_xpath(EIS.all_connections_link)
        connLink.click()

        self.debug('Waiting for page to load, getting URL')
        necessary_wait(2)
        baseURL = self.browser.current_url
        self.mainWindow = self.browser.window_handles[0]

        # Make new tab to handle the mutual connections stuff
        self.debug('Making new tab to handle mutual connections')
        self.browser.execute_script("window.open('');")
        self.mutualWindow = self.browser.window_handles[1]

        # switch back
        self.browser.switch_to.window(self.mainWindow)

        # Iterate through connections on page, then click next
        connections = self.scrapeConnections(baseURL, account_id, known=known, getMutualInfoFor=getMutualInfoFor,
                                             findLocation=withLocation, findPosition=withPosition,
                                             updateConnections=updateConnections)

        return connections

    @only_if_browser_is_running
    @connection_required
    @finish_executing
    @log_exceptions
    @authentication_required
    def scrapeConnections(self, baseURL, account_id, known: list = None, getMutualInfoFor: list = None,
                          findLocation=True, findPosition=True, updateConnections=None):
        """
        The while loop that iterates through all connections, getting their info
        """
        if known is None:
            known = []
        if getMutualInfoFor is None:
            getMutualInfoFor = []
        if updateConnections is None:
            updateConnections = []

        page = 1
        num = 0
        oldNum = 0

        while True:
            # Zoom out enough for all 10 listed connections to be on page
            self.browser.execute_script("document.body.style.zoom='20%'")
            necessary_wait(.3)  # Have to wait for script to execute

            # Get all connection cards
            conns = self.browser.find_elements_by_class_name(EIS.connection_card_info_class)

            # Iterate through them
            for connection in conns:

                # Get the name for this connection
                name = fromHTML(connection.find_element_by_class_name("name").get_attribute('innerHTML'))

                if name not in known or name in updateConnections + getMutualInfoFor:

                    # Get this person's info
                    link, pos, loc = self.getConnectionInfo(connection, pos=findPosition, loc=findLocation)

                    # # Get mutual connections if necessary
                    # if name in getMutualInfoFor:
                    #     names = self.getMutualConnections(connection)
                    # else:
                    #     names = []

                    if name in updateConnections:

                        # Get the matching connection from the database
                        prevCon = Session.query(LinkedInConnection).filter(
                            LinkedInConnection.account_id == account_id,
                            LinkedInConnection.name == name
                        )

                        # Update its values
                        if link != prevCon.url:
                            prevCon.url = link

                        if pos != prevCon.position:
                            prevCon.position = pos

                        if loc != prevCon.location:
                            prevCon.location = loc

                        # TODO: Implement mutual connections in database, if necessary, using names var from above

                        # Commit changes, log, and continue
                        Session.commit()
                        self.warning(f"Updated {name}'s information.")

                    else:
                        # Create and add the new connection
                        Session.add(
                            LinkedInConnection(
                                name=name,
                                account_id=account_id,
                                url=link,
                                location=loc,
                                status=pos
                            )
                        )

                        # Add 1 to total number of new connections, log, and continue
                        num += 1
                        self.info(f'New connection found (#{num}): {name}')

            try:
                # Finding the button that appears when there are no results
                self.browser.find_element_by_xpath(EIS.no_results_button)
                self.debug('End of connections\n')
                break
            except NoSuchElementException:
                if num > oldNum:
                    # Commit changes
                    self.info('Adding new connections to database.\n')
                    Session.commit()
                    oldNum = num
                else:
                    self.info(f'No new connections found on page {page}.\n')

                # Go to next page, and log it
                page += 1
                self.debug(f'// Switching to page {page} of connections \\\\\n')
                self.browser.get(baseURL + f'&page={page}')

        self.connectionsScraped.emit()
        self.info(f'** Scraped {num} connections and their information. **\n')

    @only_if_browser_is_running
    @connection_required
    @log_exceptions
    @authentication_required
    def getMutualConnectionsWith(self, connection):
        """
        Gets mutual connections between user and connection. connection variable is a web element, not a name
        """

        try:
            sharedStr = fromHTML(connection.find_element_by_class_name(EIS.connection_card_mutual_text).text)
        except NoSuchElementException:
            sharedStr = ""

        if not sharedStr:
            self.info('No mutual connections')
            return sharedStr

        if sharedStr.find('other shared connection') > -1:  # 3+, search the last link
            # click last link
            mutualLink = connection.find_element_by_css_selector(EIS.connection_card_mutual_link).get_attribute('href')

            self.debug('Switching to 2nd tab')
            self.browser.switch_to.window(self.mutualWindow)
            self.browser.get(mutualLink)

            # get new url
            necessary_wait(2)
            m_baseURL = self.browser.current_url
            m_page = 1

            names = []

            # similar to general while loop but only gets names
            while True:
                m_conns = self.browser.find_elements_by_class_name(EIS.connection_card_info_class)

                for m_connection in m_conns:
                    name = m_connection.find_element_by_class_name("name").get_attribute('innerHTML')
                    names.append(fromHTML(name))

                try:
                    self.browser.find_element_by_xpath(EIS.no_results_button)
                    break
                except NoSuchElementException:
                    m_page += 1
                    self.debug(f'// Tab 2: Switching to page {m_page} of mutual connections \\\\')
                    self.browser.get(m_baseURL + f'&page={m_page}')

            self.debug('Switching back to original tab')
            self.browser.switch_to.window(self.mainWindow)

        elif sharedStr.find('are shared connections') > -1:  # 2, get both names
            names = sharedStr[:-len(' are shared connections')].split(' and ')

        else:  # 1, get name
            names = [sharedStr.split(' is')[0]]

        self.info(f'Found {len(names)} mutual connection(s)')
        return names

    @only_if_browser_is_running
    @connection_required
    @log_exceptions
    @authentication_required
    def getConnectionInfo(self, connection, pos=True, loc=True):
        """
        Gets info about a connection. The connection variable is a web element, not a name
        """

        link = fromHTML(connection.find_element_by_css_selector(EIS.connection_card_profile_link).get_attribute('href'))

        if pos:
            position = fromHTML(connection.find_element_by_class_name(EIS.connection_card_position)
                                .get_attribute('innerHTML')).strip()
        else:
            position = ""

        if loc:
            location = fromHTML(connection.find_element_by_class_name(EIS.connection_card_location)
                                .get_attribute('innerHTML')[:-len(' Area')]).strip()
        else:
            location = ""

        return link, position, location

    @only_if_browser_is_running
    @connection_required
    @log_exceptions
    @authentication_required
    def refreshAll(self, known):
        """
        Updates information about all connections stored in the known list
        Known is a list of name, id tuples
        """

        self.browser.get('https://www.linkedin.com/in/me/')

        # Find connection page link, click on it
        connLink = self.browser.find_element_by_xpath(EIS.all_connections_link)
        connLink.click()

        self.debug('Waiting for page to load')
        necessary_wait(2)
        self.mainWindow = self.browser.window_handles[0]

        # Make new tab to handle the mutual connections stuff
        self.debug('Making new tab to handle mutual connections')
        self.browser.execute_script("window.open('');")
        self.mutualWindow = self.browser.window_handles[1]

        # switch back
        self.browser.switch_to.window(self.mainWindow)

        # Get the searchbar
        searchbar = self.browser.find_element_by_xpath(EIS.general_search_bar)

        package = 0
        progress = 0
        total = len(known)

        for name, conn_id in known:
            progress += 1
            self.debug(f"({progress} of {total}) Searching for {name}")

            random_uniform_wait(.6, 1)

            searchbar.clear()
            random_uniform_wait(.1, .5)
            send_keys_at_irregular_speed(searchbar, name, 1, 3, 0, .25)
            searchbar.send_keys(Keys.RETURN)

            necessary_wait(.5)

            try:
                firstResult = self.browser.find_elements_by_class_name(EIS.connection_card_info_class)[0]

                if not firstResult:
                    raise NoSuchElementException

            except (IndexError, NoSuchElementException):
                self.warning(f'It seems {name} is no longer a connection.\n')
                # TODO: Figure out if we want to flag this connection as no longer connected to account or something
                continue

            link, status, location = self.getConnectionInfo(firstResult)

            dbObj = Session.query(LinkedInConnection).filter(LinkedInConnection.id == conn_id)[0]

            # print(dbObj.name, name, dbObj.id, conn_id)
            # continue

            dbObj.url = link
            dbObj.status = status
            dbObj.location = location

            self.info(f"Updated {dbObj.name}'s information\n")

            package += 1
            if package == 20:
                # Sending 20 connection updates at a time
                Session.commit()

        Session.commit()
        self.info('Done.')

    @only_if_browser_is_running
    @connection_required
    @log_exceptions
    @authentication_required
    def requestNewConnections(self, account_id, criteria):
        """
        Requests new connections using the specified criteria
        """

        # Get the account and daily activity
        acct = Session.query(LinkedInAccount).filter(LinkedInAccount.id == account_id)[0]
        dact = LinkedInAccountDailyActivity.getToday(account_id)

        self.debug('Going to search page')
        self.browser.get('https://www.linkedin.com/in/me/')

        # Find connection page link, click on it
        connLink = self.browser.find_element_by_xpath(EIS.all_connections_link)
        connLink.click()

        necessary_wait(2)

        # Enter and apply the search criteria
        self.setSearchCriteria(criteria)

        necessary_wait(1)
        baseURL = self.browser.current_url

        page = 1
        num = 0
        lim = criteria['Request Limit']
        self.debug(f'// On page 1 of results \\\\\n')

        while True:

            # Zoom out the css enough for all 10 listed connections to be on page
            self.browser.execute_script("document.body.style.zoom='20%'")
            necessary_wait(.5)  # Have to wait for script to execute

            # Get all connection cards
            conns = self.browser.find_elements_by_class_name(EIS.connection_card)

            # Iterate through them
            for connection in conns:
                # First check the limits (against the entered amount and against the daily limit)
                if num == lim or acct.getTodaysRemainingActions() <= 0:  # lte just in case it somehow dips below
                    self.critical('Reached the local connection request limit')
                    return

                # Wait a bit
                random_uniform_wait(1, 2)

                # TODO: Determine what info we want to keep about requested connections.
                #  Keeping none other than number for the moment
                # Get the name for this connection
                name = fromHTML(connection.find_element_by_class_name("name").get_attribute('innerHTML'))

                try:
                    button = connection.find_element_by_css_selector(EIS.connect_button)
                    print(button.text)
                except NoSuchElementException:
                    # Some connections have no button or a 'Follow' button instead of a connect button
                    pass
                else:
                    if fromHTML(button.text) == 'Connect':
                        self.info(f'Requesting to connect with {name}')

                        self.browser.execute_script("arguments[0].click();", button)

                        random_uniform_wait(1, 2)

                        try:
                            confirm = self.browser.find_element_by_xpath(EIS.confirm_request_button)
                            self.browser.execute_script("arguments[0].click();", confirm)
                        except NoSuchElementException:
                            # Didn't have confirmation dialog
                            pass

                        num += 1
                        dact.connection_request_count += 1
                        Session.commit()
                        self.requestSent.emit()

            try:
                # Finding the button that appears when there are no results
                self.browser.find_element_by_xpath(EIS.no_results_button)
                self.info(f'End of results, requested {num} connections.\n')
                break
            except NoSuchElementException:
                # Go to next page, and log it
                page += 1
                self.debug(f'// Switching to page {page} of results \\\\\n')
                self.browser.get(baseURL + f'&page={page}')

    @only_if_browser_is_running
    @connection_required
    @log_exceptions
    @authentication_required
    def setSearchCriteria(self, criteria):
        """
        Sets the search criteria on the connections page
        """

        self.debug('--- Entering all criteria ---')

        # click the all filters button
        self.browser.find_element_by_xpath(EIS.all_filters_button).click()

        random_uniform_wait(1, 2)

        # unselect first connections
        box = self.browser.find_element_by_id(EIS.first_connections_box)
        self.browser.execute_script("arguments[0].click();", box)

        random_uniform_wait(.5, .9)

        if criteria['2nd Connections']:
            # select second connections
            self.debug('Choosing 2nd connections')
            box = self.browser.find_element_by_id(EIS.second_connections_box)
            self.browser.execute_script("arguments[0].click();", box)

        if criteria['3rd Connections']:
            # The 3rd connections box is disabled so this can be implemented later if we have a client who wants this
            pass

        # Enter all locations
        locationBox = self.browser.find_element_by_xpath(EIS.location_box)

        for loc in criteria['Locations']:
            random_uniform_wait(.4, .7)

            # write the location
            self.debug(f'Entering location: {loc}')
            send_keys_at_irregular_speed(locationBox, loc, 1, 3, 0, .25)

            random_uniform_wait(.3, .5)

            # select the first entry
            locationBox.send_keys(Keys.DOWN)
            random_uniform_wait(.1, .2)
            locationBox.send_keys(Keys.RETURN)
            random_uniform_wait(.3, .5)
            locationBox.clear()

        # Enter all current companies
        try:
            compBox = self.browser.find_element_by_xpath(EIS.current_company_box)
        except NoSuchElementException:
            # Some profiles don't have this option
            pass
        else:
            for comp in criteria['Companies']:
                random_uniform_wait(.4, .7)

                # write the company name
                self.debug(f'Entering company name: {comp}')
                send_keys_at_irregular_speed(compBox, comp, 1, 3, 0, .25)

                random_uniform_wait(1, 1.5)

                # select the first entry
                locationBox.send_keys(Keys.DOWN)
                random_uniform_wait(.1, .2)
                locationBox.send_keys(Keys.RETURN)
                random_uniform_wait(.3, .5)
                locationBox.clear()

        # Enter first name
        if firstName := criteria['First Name']:
            random_uniform_wait(.4, .9)
            self.debug(f'Entering first name: {firstName}')
            box = self.browser.find_element_by_id(EIS.firstname_box)
            send_keys_at_irregular_speed(box, firstName, 1, 3, 0, .25)

        # Enter last name
        if lastName := criteria['Last Name']:
            random_uniform_wait(.4, .9)
            self.debug(f'Entering last name: {lastName}')
            box = self.browser.find_element_by_id(EIS.lastname_box)
            send_keys_at_irregular_speed(box, lastName, 1, 3, 0, .25)

        # Apply the filters
        random_uniform_wait(1, 2)
        self.browser.find_element_by_xpath(EIS.apply_all_filters_button).click()


# --- QRunnables and Tasks ---------------------------------------------------------------------------------------------


class LinkedInMessenger(Task):

    def __init__(self, controller, msgTemplate, connections, setup_func=None, teardown_func=None):
        super().__init__(controller, setup = setup_func, teardown = teardown_func)
        self.msgTemplate_id = msgTemplate.id
        self.connections_ids = [connection.id for connection in connections]

    def run(self):
        self.setup()

        msgTemplate = Session.query(LinkedInMessageTemplate).get(self.msgTemplate_id)
        connections = Session.query(LinkedInConnection)\
            .filter(LinkedInConnection.id.in_(self.connections_ids))\
            .order_by(LinkedInConnection.name)
        self.controller.start()
        self.controller.messageAll(connections, usingTemplate=msgTemplate)

        try:
            self.teardown()
        except RuntimeError as e:
            if str(e).__contains__("Internal C++ object (Signals) already deleted."):
                return
            else:
                raise


class UploadConnectionCSV(QRunnable):
    """Run a function in the QThreadPool and emit the value returned in the finished signal."""

    Beacon.packageCommitted = Signal()

    def __init__(self, account_id, connections):
        super().__init__()
        self.__b = Beacon(self)
        self.connections = sorted(connections, key=lambda conn: conn[0])
        self.account_id = account_id

    def run(self):
        names = [name[0] for name in
                 Session.query(LinkedInConnection.name).filter(LinkedInConnection.account_id == self.account_id)]

        empty = 0
        package = 0

        for connection in self.connections:
            fullName = ' '.join(connection[:2])
            if fullName == ' ':
                # Sometimes there are entries with no name. We skip these but keep track of them
                empty += 1

            elif fullName not in names:

                Session.add(
                    LinkedInConnection(
                        account_id=self.account_id,
                        name=fullName,
                        email=connection[2],
                        position=connection[4] + ' at ' + connection[3],
                        date_added=parse(connection[5])
                    )
                )

                package += 1

                if package == 10:
                    Session.commit()
                    package = 0
                    self.packageCommitted.emit()

        Session.commit()
        self.finished.emit(empty)


class LinkedInIndividualConnectionScraper(Task):
    """Run a function in the QThreadPool and emit the value returned in the finished signal."""

    def __init__(self, controller, known, setup_func=None, teardown_func=None):
        super().__init__(controller, setup = setup_func, teardown = teardown_func)
        self.known = known

    def run(self):
        self.setup()
        self.controller.start()

        self.controller.refreshAll(self.known)

        self.teardown()


class LinkedInBulkConnectionScraper(Task):

    def __init__(self, controller, options, setup_func=None, teardown_func=None):
        super().__init__(controller, setup = setup_func, teardown = teardown_func)
        self.options: dict = options

    def run(self):
        self.setup()
        opts = self.options
        self.controller.start()

        known = opts.get('known')
        account_id = opts.get('accid')
        connections = self.controller.getNewConnections(account_id, known=known)

        self.teardown()


class LinkedInConnectionRequestAccepter(Task):

    def __init__(self, controller, setup_func=None, teardown_func=None):
        super().__init__(controller, setup = setup_func, teardown = teardown_func)

    def run(self):
        self.setup()
        self.controller.start()
        newCons = self.controller.acceptAllConnections()
        self.teardown()


class LinkedInConnectionRequestSender(Task):

    def __init__(self, controller, account_id, criteria, setup_func=None, teardown_func=None):
        super().__init__(controller, setup = setup_func, teardown = teardown_func)
        self.criteria: dict = criteria
        self.id = account_id

    def run(self):
        self.setup()

        self.controller.start()

        self.controller.requestNewConnections(self.id, self.criteria)

        self.teardown()
