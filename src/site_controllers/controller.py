import os
import psutil
import time
from typing import List, Iterable
from abc import ABC as AbstractBaseClass
from abc import abstractmethod

from PySide2.QtCore import QObject, Signal, Slot

from selenium.webdriver import Remote
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options

from site_controllers.exceptions import *

class Controller(QObject):
    """
    The base for any social media platform automation controller
    """

    started = Signal()
    finished = Signal()
    terminated = Signal()


    # maps string names to tuples that contain the webdriver class and path to the appropriate web driver.
    BROWSERS = {
        'Chrome': (Chrome, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "drivers", "windows")))
    }

    IMPLICIT_WAIT = 5
    HIGHLIGHT_ENABLED = False

    def __init__(self, username: str, email: str, password: str, browser: str = "Chrome", options: Iterable[str] = ()):
        """
        Initializes controller

        :param username: The username of the account to log into.
        :type username: str
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

        # store private variables first
        self._logger = None
        self._initialURL = None
        self._username = username
        self._email = email
        self._password = password

        self.initLogger()
        self.options = list(options)
        self.browser = browser


    @property
    def isRunning(self) -> bool:
        """
        :return: True if the browser is running and False otherwise.
        :rtype: bool
        """
        if not self.browser or not self.browser.service or not self.browser.service.process:
            return False

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

    def start(self):
        """Starts the controller"""

        if not self.browser:
            self.browser = self._browserConstructor(options=self.options)
            self.browser.implicitly_wait(Controller.IMPLICIT_WAIT)

        self.browser.get(self._initialURL)
        self.login(manual=False)
        self.started.emit()

    def stop(self):
        """Stops the controller by closing the browser"""
        self.browser.quit()
        while self.isRunning:
            pass
        self.browser = None

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

    @abstractmethod
    def login(self):
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

