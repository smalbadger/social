import os
import sys
import html
import logging
from datetime import timedelta, datetime

from PySide2.QtCore import Signal, QThreadPool

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException

from site_controllers.controller import Controller, Task
from site_controllers.exceptions import *
from site_controllers.decorators import *
from emails import PinValidator

from common.logging import initial_timestamp, LOG_FILES_DIR
from common.strings import onlyAplhaNumeric, equalTo, fromHTML
from common.datetime import convertToDate, convertToTime, combineDateAndTime
from common.waits import random_uniform_wait, send_keys_at_irregular_speed, necessary_wait
from common.beacon import Beacon
from common.threading import Task as ncTask

from database.general import Session
from database.linkedin import LinkedInMessage, LinkedInConnection, LinkedInMessageTemplate


#########################################################
# Element Identification Strings
#########################################################
class EIS:
    login_header                             = "header__content__heading"
    login_email_input                        = "username"
    login_password_input                     = "password"
    login_submit_button                      = "button[type=submit]"

    captcha_challenge                        = "captcha-challenge"
    pin_verification_input                   = "input__email_verification_pin"

    connection_bar                           = "msg-overlay-bubble-header"
    connection_bar_maximize                  = "overlay.maximize_connection_list_bar"
    connection_search                        = "msg-overlay-list-bubble-search__search-typeahead-input"
    connection_message_select                = "//h4[text()={concat}]/../.."

    message_scroll_box                       = "msg-s-message-list"
    message_editor                           = "msg-form__contenteditable"
    message_send                             = "msg-form__send-button"
    message_item                             = "msg-s-message-list__event"
    message_date                             = "msg-s-message-list__time-heading"
    message_time                             = "msg-s-message-group__timestamp"
    message_author                           = "msg-s-message-group__name"
    message_body                             = "msg-s-event-listitem__body"

    profile_link                             = '//span[text()="{connectionName}"]./..'
    connection_request_accept_button         = "//button[@class='invitation-card__action-btn artdeco-button" \
                                               "artdeco-button--2 artdeco-button--secondary ember-view']"

    profile_picture                          = '//div[@data-control-name="identity_profile_photo"]/..'
    all_connections_link                     = '//a[@data-control-name="topcard_view_all_connections"]'
    connection_card_info_class               = 'search-result__info'
    connection_card_profile_link             = '[data-control-name="search_srp_result"]'
    connection_card_position                 = "subline-level-1"
    connection_card_location                 = "subline-level-2"
    connection_card_mutual_text              = 'search-result__social-proof-count'
    connection_card_mutual_link              = '[data-control-name="view_mutual_connections"]'
    no_results_button                        = '//button[@data-test="no-results-cta"]'


class LinkedInException(ControllerException):
    def __init__(self, msg):
        ControllerException.__init__(self, msg)

class LinkedInController(Controller):
    """
    The controller for LinkedIn
    """

    Beacon.connectionsScraped = Signal(dict)
    Beacon.messageSent = Signal(int, int) # connection id, message id

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
        self.info(f"Created LinkedIn controller for {self._profile_name}")

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

    @log_exceptions
    @ensure_browser_is_running
    def auth_check(self):
        # TODO: Improve this check
        return "Login" not in self.browser.title and "Sign in" not in self.browser.title

    @finish_executing  # TODO: Here for testing, remove later
    @log_exceptions
    @ensure_browser_is_running
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
                self.info(f"Entering email: {self._email}")
                send_keys_at_irregular_speed(self.browser.find_element_by_id(EIS.login_email_input), self._email, 1, 3, 0, .25)

            if self._password:
                self.info(f"Entering password: {'*'*len(self._password)}")
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
                    self.info(f"Retrieved PIN: {pin}")
                    pin_inputs[0].send_keys(pin + Keys.RETURN)
                    entered = True

                timeout = timedelta(minutes=1)
                self.info("Detected pin validation method. Attempting to retrieve PIN from email.")

                task = ncTask(lambda: PinValidator().get_pin(self._profile_name, self._email, timeout))
                task.finished.connect(enterPIN)
                QThreadPool.globalInstance().start(task)

                start = datetime.now()
                while True:
                    pin_inputs = self.browser.find_elements_by_id(EIS.pin_verification_input)
                    if not pin_inputs and not entered:
                        self.info('PIN entered manually.')
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

        if not self.auth_check():
            raise AuthenticationException("For some reason, we couldn't leave the login page.")

    @log_exceptions
    @authentication_required
    def maximizeConnectionPopup(self):
        """opens the connection popup"""
        self.info("Finding connection list bar")
        possible_connection_bars = self.browser.find_elements_by_class_name(EIS.connection_bar)
        for possibility in possible_connection_bars:
            if possibility.get_attribute("data-control-name") == EIS.connection_bar_maximize:
                self.info("maximizing the connection list")
                possibility.click()

    @log_exceptions
    @authentication_required
    def searchForConnectionInPopup(self, person: str):
        """Only search for a person in the popup connections bar."""
        self.info(f"Searching for {person} in messages")

        # make sure conversation list is visible
        searchbox = WebDriverWait(self.browser, 3).until(
            EC.visibility_of_element_located((By.ID, EIS.connection_search)))
        self.info("The search field has been found")
        self.highlightElement(searchbox)
        self.info("Clearing the search field")
        searchbox.send_keys(Keys.CONTROL + "a")
        searchbox.send_keys(Keys.DELETE)
        self.info(f"Entering name in search field: {person}")
        searchbox.send_keys(person)
        searchbox.send_keys(Keys.RETURN)

    @log_exceptions
    @authentication_required
    def selectConnectionFromPopup(self, person: str):
        """Select a person from the popup connection bar assuming they're already shown."""
        self.info(f"Finding link to {person}'s list element")
        concat = "concat(\"" + "\", \"".join(list(person)) + "\")"
        necessary_wait(1)
        target_account = WebDriverWait(self.browser, 10) \
            .until(EC.element_to_be_clickable((By.XPATH, EIS.connection_message_select.format(concat=concat))))
        self.info(f"scrolling through results to {person}")
        ActionChains(self.browser).move_to_element(target_account).perform()
        self.highlightElement(target_account)
        self.info("Clicking on connection to open messaging box")
        target_account.click()

    @log_exceptions
    @authentication_required
    def openConversationWith(self, person: str):
        """Searches messages for the name entered, and gets the first person from the list"""
        self.searchForConnectionInPopup(person)
        self.selectConnectionFromPopup(person)

    @log_exceptions
    @authentication_required
    def closeAllChatWindows(self):
        """Closes all open chat windows"""
        # I was having trouble iterating over all chat windows and closing them because when one closes, the others
        # become detached or something. Refreshing is a more robust way of closing the windows.
        self.info("Clearing all open message dialogs to avoid mis-identification")
        self.browser.refresh()

    @finish_executing
    @log_exceptions
    @authentication_required
    def sendMessageTo(self, connection: LinkedInConnection, message: str, template):
        """Sends a message to the person."""
        person = connection.name

        msg_details = f"""Sending message:

                To: {person}
                From: {self._profile_name}
                Content: {message}
                """

        self.info(msg_details)

        if connection.account.dailyActivityLimitReached():
            self.critical(f"Daily activity limit reached! The above message was not sent.")
            return

        self.closeAllChatWindows()
        self.openConversationWith(person)

        self.info("Finding the message box")
        msg_box = self.browser.find_element_by_class_name(EIS.message_editor)
        self.highlightElement(msg_box)
        self.info(f"Typing the message: {message}")
        msg_box.send_keys(message)
        self.info("Finding the submit button")
        msg_send = self.browser.find_element_by_class_name(EIS.message_send)
        self.highlightElement(msg_send)
        self.info("Sending the message")
        msg_send.click()

        self.info("Verifying the message was sent")
        now = datetime.now()
        msg, timestamp = self.getLastMessageWithConnection(person, assumeConversationIsOpened=True)
        if not msg or not equalTo(msg, message, normalize_whitespace=True) or timestamp - now > timedelta(minutes=1):
            self.critical(f"The last message was '{msg}' and it was sent at {timestamp}")
            raise MessageNotSentException(f"The message '{message}' was not sent to {person}")
        self.info("The message was sent successfully")

        self.info("Updating database")
        msg = template.createMessageTo(connection)
        msg.recordAsDelivered()
        self.messageSent.emit(connection.id, msg.id)
        Session.add(msg)
        Session.commit()

    @log_exceptions
    @authentication_required
    def messageAll(self, connections: list, usingTemplate, checkPastMessages=True):
        """Messages all connections with the template usingTemplate (a query object)"""
        # TODO: Check for past messages sent by this bot

        for connection in connections:  # each connection is a query object

            # Checking database to see if template was already sent to user
            if checkPastMessages:
                previouslySentMessages = Session.query(LinkedInMessage).filter(
                    LinkedInMessage.recipient_connection_id == connection.id,
                    LinkedInMessage.template_id == usingTemplate.id
                )
                alreadySent = previouslySentMessages.count()
            else:
                alreadySent = 0

            if alreadySent:
                self.warning(f"Skipping {connection.name} because the message has already been sent to them.")
            elif not usingTemplate.isValid(connection):
                self.warning(f"Skipping {connection.name} because the message template was invalid for this connection.")
            else:
                msg = usingTemplate.fill(connection)
                self.sendMessageTo(connection, msg, usingTemplate)

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

        self.info(f"Fetching conversation history with {person}")
        if not assumeConversationIsOpened:
            self.closeAllChatWindows()
            self.openConversationWith(person)

        prevHTML = ""
        necessary_wait(1)
        for i in range(round(numMessages / 20)):
            scroll_areas = self.browser.find_elements_by_class_name(EIS.message_scroll_box)
            if scroll_areas:
                scroll_area = scroll_areas[0]
                self.info(f"Loading previous messages with {person}...")
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

        self.info(f"{len(history)} messages with {person} found - returning {min(len(history), numMessages)}")
        wanted_history = history[-numMessages:]
        return wanted_history

    @log_exceptions
    @authentication_required
    def acceptAllConnections(self) -> list:
        """Accepts all connections and returns them as a list of (name, profileLink) tuples"""

        accepted = []

        self.info("Switching to network page")
        self.browser.get('https://www.linkedin.com/mynetwork/')

        self.info('Getting connection requests')
        try:
            acceptButtons = self.browser.find_elements_by_xpath(EIS.connection_request_accept_button)

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
            profLinkElement = self.browser.find_element_by_xpath(EIS.profile_link.format(connectionName = connectionName))
            profLink = profLinkElement.get_attribute('href')
            button.click()
            accepted.append((connectionName, profLink))

        return accepted

    @log_exceptions
    @authentication_required
    def getNewConnections(self, known: list = None, getMutualInfoFor: list = None,
                          withLocation=True, withPosition=True, updateConnections=None) -> dict:
        """
        Gets all contacts and returns them in a dictionary
        :param known: A list of currently stored connections
        :param getMutualInfoFor: A list of connections you want the mutual connections info for
        :param withLocation: whether to store location information about the connections
        :param withPosition: whether to store job/position info about the connections
        :param updateConnections: update all info for those in this list
        """

        self.info('Getting all connections')

        # Find profile pic, click on it
        profile = self.browser.find_element_by_xpath(EIS.profile_picture)
        profile.click()

        # Find connection page link, click on it
        connLink = self.browser.find_element_by_xpath(EIS.all_connections_link)
        connLink.click()

        self.info('Waiting for page to load, getting URL')
        necessary_wait(2)
        baseURL = self.browser.current_url
        self.mainWindow = self.browser.window_handles[0]

        # Make new tab to handle the mutual connections stuff
        self.info('Making new tab to handle mutual connections')
        self.browser.execute_script("window.open('');")
        self.mutualWindow = self.browser.window_handles[1]

        # switch back
        self.browser.switch_to.window(self.mainWindow)

        # Iterate through connections on page, then click next
        connections = self.scrapeConnections(baseURL, known=known, getMutualInfoFor=getMutualInfoFor,
                                             location=withLocation, position=withPosition,
                                             updateConnections=updateConnections)

        return connections

    @log_exceptions
    @authentication_required
    def scrapeConnections(self, baseURL,  known: list = None, getMutualInfoFor: list = None,
                          location=True, position=True, updateConnections=None):
        """
        The while loop that iterates through all connections, getting their info
        """
        if known is None:
            known = []
        if getMutualInfoFor is None:
            getMutualInfoFor = []
        if updateConnections is None:
            updateConnections = []

        connections = {}
        page = 1

        while True:
            conns = self.browser.find_elements_by_class_name(EIS.connection_card_info_class)
            for connection in conns:

                name = fromHTML(connection.find_element_by_class_name("name").get_attribute('innerHTML'))

                if name not in known or name in updateConnections + getMutualInfoFor:
                    self.info('')
                    self.info(f'--- Getting information about {name} ---')

                    profileLink, pos, loc = self.getConnectionInfo(connection, pos=position, loc=location)

                    if name in getMutualInfoFor:
                        names = self.getMutualConnections(connection)
                    else:
                        names = []

                    connections[name] = {
                        'link': profileLink,
                        'position': pos,
                        'location': loc,
                        'mutual': names
                    }

            try:
                self.browser.find_element_by_xpath(EIS.no_results_button)
                break
            except NoSuchElementException:
                page += 1
                self.info(f'// Switching to page {page} of connections \\\\')
                self.browser.get(baseURL + f'&page={page}')

        self.info('')
        self.info('** Scraped all connections and their information. **')
        self.info('')

        self.connectionsScraped.emit(connections)
        return connections

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

            self.info('Switching to 2nd tab')
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
                    self.info(f'// Tab 2: Switching to page {m_page} of mutual connections \\\\')
                    self.browser.get(m_baseURL + f'&page={m_page}')

            self.info('Switching back to original tab')
            self.browser.switch_to.window(self.mainWindow)

        elif sharedStr.find('are shared connections') > -1:  # 2, get both names
            names = sharedStr[:-len(' are shared connections')].split(' and ')

        else:  # 1, get name
            names = [sharedStr.split(' is')[0]]

        self.info(f'Found {len(names)} mutual connection(s)')
        return names

    @log_exceptions
    @authentication_required
    def getConnectionInfo(self, connection, pos=True, loc=True):
        """
        Gets info about a connection. The connection variable is a web element, not a name
        """

        self.info('Getting profile link')
        profileLink = fromHTML(connection.find_element_by_css_selector(EIS.connection_card_profile_link)
                               .get_attribute('href'))

        if pos:
            self.info('Getting employment information')
            position = fromHTML(connection.find_element_by_class_name(EIS.connection_card_position)
                                .get_attribute('innerHTML')).strip()
        else:
            position = ""

        if loc:
            self.info('Getting general location')
            location = fromHTML(connection.find_element_by_class_name(EIS.connection_card_location)
                                .get_attribute('innerHTML')[:-len(' Area')]).strip()
        else:
            location = ""

        return profileLink, position, location


class LinkedInMessenger(Task):

    def __init__(self, controller, msgTemplate, connections, setup_func=None, teardown_func=None):
        super().__init__(controller, setup = setup_func, teardown = teardown_func)
        self.msgTemplate_id = msgTemplate.id
        self.connections_ids = [connection.id for connection in connections]

    def run(self):
        self.setup()

        msgTemplate = Session.query(LinkedInMessageTemplate).get(self.msgTemplate_id)
        connections = Session.query(LinkedInConnection).filter(LinkedInConnection.id.in_(self.connections_ids)).all()
        self.controller.start()
        self.controller.messageAll(connections, usingTemplate=msgTemplate)

        self.teardown()


class LinkedInSynchronizer(Task):

    def __init__(self, controller, options, setup_func=None, teardown_func=None):
        super().__init__(controller, setup = setup_func, teardown = teardown_func)
        self.options: dict = options

    def run(self):
        self.setup()
        opts = self.options
        self.controller.start()

        if opts.get('accept new'):
            newCons = self.controller.acceptAllConnections()

            # TODO: Do necessary things to handle new connections
            self.controller.browser.get("https://www.linkedin.com/feed/")

        if opts.get('connections'):
            known = opts.get('known')
            connections = self.controller.getNewConnections(known=known)
            # TODO: Add connections scraping/syncing here. currently repopulates the all contacts list

        if opts.get('messages'):
            # TODO: Synchronize messages
            pass

        self.teardown()

