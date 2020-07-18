from functools import wraps


def ensureBrowserIsRunning(func):
    """
    Makes the browser is started before a function is called
    """
    @wraps(func)
    def check(*args, **kwargs):
        controller = args[0]
        if not controller.isRunning:
            controller.start()

        func(*args, **kwargs)

    return check


def authentication_required(func):
    """
    A decorator for most functions in the site_controllers. Ensures a user is logged in before executing any functions.
    """

    @wraps(func)
    def check(*args, **kwargs):
        controller = args[0]

        if "Login" in controller.browser.title or "Sign in" in controller.browser.title:
            controller.login()

        # TODO: Integration email PinValidator in here

        func(*args, **kwargs)

    return check
