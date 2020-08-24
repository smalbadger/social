from functools import wraps
import time
from subprocess import check_call
import common.authenticate as inst
import logging
from ping3 import ping


def ensure_browser_is_running(func):
    """Makes the browser is started before a function is called"""
    @wraps(func)
    def check(*args, **kwargs):
        controller = args[0]

        if not controller.isRunning:
            controller.start()

        return func(*args, **kwargs)

    return check

def authentication_required(func):
    """Ensures a user is logged in before executing any functions."""

    @wraps(func)
    def check(*args, **kwargs):
        controller = args[0]

        if not controller.auth_check():
            controller.login()

        return func(*args, **kwargs)

    return check

def log_exceptions(func):
    """Log all exceptions"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        controller = args[0]

        try:
            return func(*args, **kwargs)
        except Exception as e:
            if not controller.closing:  # Suppresses log of inevitable final http errors when closing manually
                args[0].exception(e)
            # raise e

    return wrapper

def finish_executing(func):
    """
    Makes sure the function finishes before the application is force-quit.
    Use as little as possible, only on the functions that need to finish to keep data intact
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        inst.Lock = True
        x = func(*args, **kwargs)
        inst.Lock = False
        return x

    return wrapper

def connection_required(func, url="google.com", timeout=10, retries=3):
    """
    Makes sure we have access to a particular server before continuing
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        controller = args[0]

        live = False
        for n in range(retries):

            if ping(url, timeout=timeout):
                live = True
                break

            controller.warning("Not connected to the internet")

            if n < retries-1:
                controller.info("Attempting to connect")

            check_call(['restartwireless.bat'])
            time.sleep(3)
            controller.browser.refresh()


        if not live:
            exit(200)

        return func(*args, **kwargs)

    return wrapper