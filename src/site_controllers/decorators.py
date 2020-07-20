from functools import wraps


def ensure_browser_is_running(func):
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

        if not controller.auth_check():
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

def log_all_exceptions(Cls):
    """Apply the log_exceptions decorator to every instance method"""


    def log_exceptions(func, controller):
        """Log all exceptions"""

        @wraps(func)
        def wrapper(*args, **kwargs):

            try:
                return func(*args, **kwargs)
            except Exception as e:
                controller.exception(e)
                raise e

        return wrapper


    class NewCls(object):
        def __init__(self, *args, **kwargs):
            self.oInstance = Cls(*args, **kwargs)

        def __getattribute__(self, s):
            """
            this is called whenever any attribute of a NewCls object is accessed. This function first tries to
            get the attribute off NewCls. If it fails then it tries to fetch the attribute from self.oInstance (an
            instance of the decorated class). If it manages to fetch the attribute from self.oInstance, and
            the attribute is an instance method then `log_exceptions` is applied.
            """
            try:
                x = super(NewCls, self).__getattribute__(s)
            except AttributeError:
                pass
            else:
                return x

            x = self.oInstance.__getattribute__(s)
            if type(x) == type(self.__init__):  # it is an instance method
                return log_exceptions(x, self.oInstance)  # this is equivalent of just decorating the method with log_exceptions
            else:
                return x

    return NewCls