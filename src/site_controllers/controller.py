import os
import psutil
from typing import List, Iterable
from abc import ABC as AbstractBaseClass
from abc import abstractmethod

from selenium.webdriver import Remote
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options


class ControllerException(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)


class Controller(AbstractBaseClass):
    """
    The base for any social media platform automation controller
    """

    # maps string names to tuples that contain the webdriver class and path to the appropriate web driver.
    BROWSERS = {
        'Chrome': (Chrome, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "drivers", "windows")))
    }

    IMPLICIT_WAIT = 5

    def __init__(self, email: str, password: str, browser: str = "Chrome", options: Iterable[str] = ()):
        """
        Initializes controller

        :param email: The emails OR username of the account to log into.
        :type email: str
        :param password: The password of the account to log into.
        :type password: str
        :param browser: Either an existing browser instance or a string the the name of the browser to create an instance
        :type browser: selenium.webdriver OR str
        :param options: Arguments to use when launching the browser
        :type options: Iterable[str]
        """

        self.options = list(options)
        self.browser = browser
        self._initialURL = None
        self._email = email
        self._password = password

    @property
    def isRunning(self) -> bool:
        """
        :return: True if the browser is running and False otherwise.
        :rtype: bool
        """
        try:
            if not self._browser:
                return False
        except AttributeError:
            return False

        driver_process = psutil.Process(self._browser.service.process.pid)
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
        :rtype: Remote
        """
        try:
            if self._browser:
                return self._browser
        except AttributeError:
            pass
        raise ControllerException("The browser is not set")

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
            browserConstructor, driverpath = Controller.BROWSERS[browser]
            os.environ["PATH"] += ";" + driverpath
            self._browser = browserConstructor(options=self.options)
            self._browser.implicitly_wait(Controller.IMPLICIT_WAIT)

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
        self.browser.get(self._initialURL)
        self.login()

    def stop(self):
        """Stops the controller by closing the browser"""
        self.browser.close()
        self.browser = None

    @abstractmethod
    def login(self):
        """
        Must be overridden in subclasses. Raises error here.
        """
        raise ControllerException('Override the login function in the Controller subclass you are using.')
