from functools import wraps


def ensureBrowserIsRunning(func):
    """Makes the browser is started before a function is called"""
    @wraps(func)
    def check(*args, **kwargs):
        controller = args[0]
        if not controller.isRunning:
            controller.start()

        func(*args, **kwargs)

    return check


def authentication_required(func):
    """Ensures a user is logged in before executing any functions."""

    @wraps(func)
    def check(*args, **kwargs):
        controller = args[0]

        if "Login" in controller.browser.title or "Sign in" in controller.browser.title:
            controller.login()

        func(*args, **kwargs)

    return check


def print_page_on_exception(func):
    """If an exception occurs, print the page HTML"""

    @wraps(func)
    def check(*args, **kwargs):
        controller = args[0]

        try:
            func(*args, **kwargs)
        except Exception as e:
            print(controller.browser.page_source)
            raise e

    return check