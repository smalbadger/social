from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options


class Controller:
    """
    The base for any social media platform automation controller
    """

    BROWSERS = {
        'Chrome': Chrome
    }

    def __init__(self, browser: str, args: list = None):
        """
        Initializes a controller.

        :param browser: A string describing the browser to use
        :type browser: str
        :param args: Arguments to use when launching the browser
        :type args: list
        """

        if args is None:  # Apparently this is needed bc [] is mutable, no idea what that means
            args = []

        self.options = Options()

        for argument in args:
            self.options.add_argument(argument)

        self.browserCall = Controller.BROWSERS[browser]
        self.browser = None
        self.initURL = None
        self.isRunning = False

    def start(self):
        """
        Starts the controller
        """

        if not self.isRunning:
            self.isRunning = True
            self.browser = self.browserCall(options=self.options)
            self.browser.get(self.initURL)
            self.login()

    def stop(self):
        """
        Stops the controller by closing the browser
        """

        if self.isRunning:
            self.isRunning = False

            try:
                self.browser.close()
            except:
                print("Couldn't close the browser, probably because it was already closed.")

    def login(self):
        """
        Must be overridden in subclasses. Raises error here.
        """
        raise Exception('Override the login function in the Controller subclass you are using.')

