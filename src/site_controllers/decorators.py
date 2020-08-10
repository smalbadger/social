from functools import wraps
import common.instance as inst

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

        try:
            return func(*args, **kwargs)
        except Exception as e:
            args[0].exception(e)
            # raise e

    return wrapper


def finish_executing(func):
    # Makes sure the function finishes before the application is force-quit.
    # Use as little as possible, only on the functions that need to finish to keep data intact

    @wraps(func)
    def wrapper(*args, **kwargs):
        inst.Lock = True
        x = func(*args, **kwargs)
        inst.Lock = False
        return x

    return wrapper

# def log_all_exceptions(Cls):
#     """
#     Apply the log_exceptions decorator to every instance method
#
#     WARNING: This causes issues with accessing class variables! To access class variables of classes where this
#              decorator is applied, the .innerCls attribute must be used. For instance:
#              LinkedInController.innerCls.CRITICAL_LOGIN_INFO
#     """
#
#
#
#     class NewCls(object):
#
#         innerCls = Cls
#
#         def __init__(self, *args, **kwargs):
#             self.oInstance = Cls(*args, **kwargs)
#
#         def __getattribute__(self, s):
#             """
#             this is called whenever any attribute of a NewCls object is accessed. This function first tries to
#             get the attribute off NewCls. If it fails then it tries to fetch the attribute from self.oInstance (an
#             instance of the decorated class). If it manages to fetch the attribute from self.oInstance, and
#             the attribute is an instance method then `log_exceptions` is applied.
#             """
#             print("wtf", flush=True)
#             try:
#                 x = super(NewCls, self).__getattribute__(s)
#             except AttributeError:
#                 pass
#             else:
#                 return x
#
#             x = self.oInstance.__getattribute__(s)
#             if type(x) == type(self.__init__):  # it is an instance method
#                 print("wrap", s)
#                 return log_exceptions(x, self.oInstance)  # this is equivalent of just decorating the method with log_exceptions
#             else:
#                 return x
#
#
#     return NewCls
