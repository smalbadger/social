import os
import psutil
import time
from typing import List, Iterable
from abc import ABC as AbstractBaseClass
from abc import abstractmethod

from PySide2.QtCore import QRunnable

from selenium.webdriver import Remote
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options

from site_controllers.exceptions import *
from common.beacon import Beacon


class Controller(AbstractBaseClass):
    """
    The base for any social media platform automation controller
    """

    # maps string names to tuples that contain the webdriver class and path to the appropriate web driver.
    BROWSERS = {
        'Chrome': (Chrome, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "drivers", "windows")))
    }

    IMPLICIT_WAIT = 1
    HIGHLIGHT_ENABLED = True

    def __init__(self, profile_name: str, email: str, password: str, browser: str = "Chrome", options: Iterable[str] = ()):
        """
        Initializes controller

        :param profile_name: The profile name of the account to log into.
        :type profile_name: str
        :param email: The emails of the account to log into.
        :type email: str
        :param password: The password of the account to log into.
        :type password: str
        :param browser: Either an existing browser instance or the name of the browser to create an instance
        :type browser: selenium.webdriver OR str
        :param options: Arguments to use when launching the browser
        :type options: Iterable[str]
        """

        super().__init__()
        self.__b = Beacon(self)

        # store private variables first
        self._logger = None
        self._initialURL = None
        self._profile_name = profile_name
        self._email = email
        self._password = password
        self._criticalLoginInfo = ()

        self.initLogger()
        self.options = list(options)
        self.browser = browser

        self.manualClose = False

    def checkForValidConfiguration(self):
        """
        Determines if the controller configuration is Valid

        :raises InvalidOptionsException: if invalid options are provided
        """
        if self.isManualLoginNeeded() and "headless" in self.options.arguments:
            missingCredentials = ', '.join(self.getMissingCriticalLoginInfo())
            raise InvalidOptionsException("The controller cannot be started in headless mode because the following "
                                          f"credentials were not provided: {missingCredentials}")
        # TODO: Add more checks as necessary

    def isManualLoginNeeded(self):
        manual = False
        for field in self._criticalLoginInfo:
            manual = manual or not self.__getattribute__(f"_{field}")
        return manual

    def getMissingCriticalLoginInfo(self):
        missingFields = []
        for field in self._criticalLoginInfo:
            if not self.__getattribute__(f"_{field}"):
                missingFields.append(field)
        return missingFields

    def start(self):
        """Starts the controller"""

        self.info('')
        self.info("Starting Controller")

        if self.isRunning:
            return

        if not self.browser:
            self.browser = self._browserConstructor(options=self.options)
            self.browser.implicitly_wait(Controller.IMPLICIT_WAIT)

        self.browser.get(self._initialURL)
        self.login(manual=self.isManualLoginNeeded())

    def stop(self):
        """Stops the controller by closing the browser"""
        if self.isRunning:
            self.browser.quit()

            while self.isRunning:
                pass
            self.browser = None

            self.info("Stopped browser")

    #############################################################
    #  Abstract Methods
    #############################################################

    @abstractmethod
    def login(self, manual=False):
        """Process taken to login"""
        pass

    @abstractmethod
    def initLogger(self):
        """Initialize the logger appropriately"""
        pass

    @abstractmethod
    def auth_check(self):
        """Quickly check if user is authenticated"""
        pass

    #############################################################
    #  Properties
    #############################################################

    @property
    def isRunning(self) -> bool:
        """
        :return: True if the browser is running and False otherwise.
        :rtype: bool
        """
        if not self.browser or not self.browser.service or not self.browser.service.process:
            return False

        try:
            driver_process = psutil.Process(self.browser.service.process.pid)
            if driver_process.is_running():
                children_processes = driver_process.children()
                if children_processes:
                    child_process = children_processes[0]
                    if child_process.is_running():
                        return True
                    else:
                        child_process.kill()
            return False

        except:  # If process no longer exists
            return False

    @property
    def browser(self) -> Remote:
        """
        :return: Gets the browser from the controller
        :rtype: Remote or NoneType
        """
        try:
            if self._browser:
                return self._browser
        except AttributeError:
            return None

    @browser.setter
    def browser(self, browser):
        """
        :param browser: Either an existing browser object or a key from the Controller.BROWSERS dictionary
        """
        if self.isRunning:
            raise ControllerException("This controller has another running browser that must be terminated first")

        if isinstance(browser, str):
            if browser not in Controller.BROWSERS.keys():
                raise ControllerException(f"{browser} is not a supported Browser")
            self._browserConstructor, driverpath = Controller.BROWSERS[browser]
            if driverpath not in os.environ['PATH']:
                os.environ["PATH"] += ";" + driverpath

        elif isinstance(browser, Remote):
            self._browser = browser

    @property
    def options(self):
        try:
            return self._options
        except NameError:
            raise ControllerException("No options are set for this controller.")

    @options.setter
    def options(self, args: List[str]):
        """
        :param args: List of string arguments for the browser
        """
        self._options = Options()
        for argument in args:
            self._options.add_argument(argument)

    #############################################################
    #  Element Operations
    #############################################################
    def highlightElement(self, element, effect_time=1, border_color="red", background_color="yellow", text_color="blue", border=2):
        """Highlights (blinks) a Selenium Webdriver element"""

        if not Controller.HIGHLIGHT_ENABLED:
            return

        def apply_style(s):
            self.browser.execute_script("arguments[0].setAttribute('style', arguments[1]);", element, s)

        original_style = element.get_attribute('style')

        flash_count = 10
        for i in range(effect_time * flash_count):
            time.sleep(effect_time / flash_count / 2)
            apply_style("border: {0}px dashed {1}; background-color: {2}; color: {3};".format(border, border_color, background_color, text_color))
            time.sleep(effect_time / flash_count / 2)
            apply_style(original_style)

    def getInnerHTML(self, element):
        """
        Gets the inner HTML of a selenium element. If the element has no children, the text inside the element will be
        returned.
        """
        return element.get_attribute('innerHTML').replace('<!---->', '').strip()

    def setInnerText(self, element, innerText):
        """Sets the innerText of an element"""
        self.browser.execute_script(f"arguments[0].innerText = '{innerText}'", element)

    #############################################################
    #  Logging Shortcuts
    #############################################################
    def debug(self, *args, **kwargs):
        self._logger.debug(*args, **kwargs)

    def info(self, *args, **kwargs):
        self._logger.info(*args, **kwargs)

    def warning(self, *args, **kwargs):
        self._logger.warning(*args, **kwargs)

    def error(self, *args, **kwargs):
        self._logger.error(*args, **kwargs)

    def critical(self, *args, **kwargs):
        self._logger.critical(*args, **kwargs)

    def exception(self, *args, **kwargs):
        self._logger.exception(*args, **kwargs)


class Task(QRunnable):
    """Subclass this to create a task that can be run from the GUI."""

    def __init__(self, controller: Controller, setup=None, teardown=None):
        super().__init__()
        self.controller = controller

        self._setup = setup
        self._teardown = teardown

    def setup(self):
        if self._setup:
            self._setup()

    def teardown(self):
        if self._teardown:
            self._teardown()
