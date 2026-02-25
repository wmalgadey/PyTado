"""Tado exceptions."""


class TadoException(Exception):
    """Base exception class for Tado."""


class TadoNotSupportedException(TadoException):
    """Exception to indicate a requested action is not supported by Tado."""


class TadoCredentialsException(TadoException):
    """Exception to indicate something with credentials"""


class TadoNoCredentialsException(TadoCredentialsException):
    """Exception to indicate missing credentials"""


class TadoWrongCredentialsException(TadoCredentialsException):
    """Exception to indicate wrong credentials"""


class TadoRateLimitException(TadoException):
    """Exception to indicate API rate limit has been exceeded."""
