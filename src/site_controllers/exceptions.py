class ControllerException(Exception):
    def __init__(self, msg):
        super().__init__(msg)

class InvalidOptionsException(ControllerException):
    def __init__(self, msg):
        super().__init__(msg)

class MessageNotSentException(ControllerException):
    def __init__(self, msg):
        super().__init__(msg)

class BotDetectedException(Exception):
    def __init__(self, msg):
        super().__init__(msg)

class NotConnectedException(ControllerException):
    def __init__(self, msg):
        super().__init__(msg)

class AuthenticationException(ControllerException, PermissionError):
    def __init__(self, msg):
        super().__init__(msg)

class InvalidCredentialsException(AuthenticationException):
    def __init__(self, msg):
        super().__init__(msg)

class SecurityVerificationException(AuthenticationException):
    def __init__(self, msg):
        super().__init__(msg)

class CaptchaTimeoutException(SecurityVerificationException, TimeoutError):
    def __init__(self, msg):
        super().__init__(msg)

class PINTimeoutException(SecurityVerificationException, TimeoutError):
    def __init__(self, msg):
        super().__init__(msg)

class CaptchaBotDetectedException(SecurityVerificationException, BotDetectedException):
    def __init__(self, msg):
        super().__init__(msg)
