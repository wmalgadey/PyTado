"""
PyTado interface abstraction to use app.tado.com or hops.tado.com
"""

import functools
import warnings
from typing import Any, Callable, TypeVar, cast

import requests

import PyTado.interface.api as API
from PyTado.exceptions import TadoException
from PyTado.http import DeviceActivationStatus, Http

F = TypeVar("F", bound=Callable[..., Any])  # Type variable for function


def deprecated(new_func_name: str) -> Callable[[F], F]:
    """
    A decorator to mark functions as deprecated. It will result in a warning being emitted
    when the function is used, advising the user to use the new function instead.

    Args:
        new_func_name (str): The name of the new function that should be used instead.

    Returns:
        Callable[[F], F]: A decorator that wraps the deprecated function and emits a warning.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            warnings.warn(
                f"The '{func.__name__}' method is deprecated, use '{new_func_name}' instead. "
                "Deprecated methods will be removed with 1.0.0.",
                DeprecationWarning,
                stacklevel=2,
            )
            return getattr(args[0], new_func_name)(*args[1:], **kwargs)

        return cast(F, wrapper)

    return decorator


class Tado:
    """Interacts with a Tado thermostat via public API.

    Example usage: t = Tado()
                   t.device_activation() # Activate device
                   t.get_climate(1) # Get climate, zone 1.
    """

    def __init__(
        self,
        token_file_path: str | None = None,
        saved_refresh_token: str | None = None,
        http_session: requests.Session | None = None,
        debug: bool = False,
        user_agent: str | None = None,
    ):
        """
        Initializes the interface class.

        Args:
            token_file_path (str | None, optional): Path to a file which will be used to persist
                the refresh_token token. Defaults to None.
            saved_refresh_token (str | None, optional): A previously saved refresh token.
                Defaults to None.
            http_session (requests.Session | None, optional): An optional HTTP session to use for
                requests (can be used in unit tests). Defaults to None.
            debug (bool, optional): Flag to enable or disable debug mode. Defaults to False.
            user_agent (str | None): Optional user-agent header to use for the HTTP requests.
                If None, a default user-agent PyTado/<PyTado-version> will be used.
        """

        self._http = Http(
            token_file_path=token_file_path,
            saved_refresh_token=saved_refresh_token,
            http_session=http_session,
            debug=debug,
            user_agent=user_agent,
        )
        self._api: API.Tado | API.TadoX | None = None
        self._debug = debug

    def __getattr__(self, name: str) -> Any:
        """
        Delegate the called method to api implementation (hops_tado.py or my_tado.py).

        Args:
            name: The name of the attribute/method being accessed

        Returns:
            Any: The delegated attribute or method from the underlying API implementation

        Raises:
            TadoException: If the API is not initialized
            AttributeError: If the attribute doesn't exist on the API implementation
        """
        self._ensure_api_initialized()
        return getattr(self._api, name)

    def device_verification_url(self) -> str | None:
        """
        Returns the URL for device verification.

        Returns:
            str | None: The verification URL or None if not available
        """
        return self._http.device_verification_url

    def device_activation_status(self) -> DeviceActivationStatus:
        """
        Returns the status of the device activation.

        Returns:
            DeviceActivationStatus: The current activation status of the device
        """
        return self._http.device_activation_status

    def device_activation(self) -> None:
        """
        Activates the device and initializes the API client.

        Raises:
            TadoException: If device activation fails
        """
        self._http.device_activation()
        self._ensure_api_initialized()

    def get_refresh_token(self) -> str | None:
        """
        Retrieve the refresh token from the current api connection.

        Returns:
            str | None: The current refresh token, or None if not available.
        """
        return self._http.refresh_token

    def _ensure_api_initialized(self) -> None:
        """
        Ensures the API client is initialized.

        Raises:
            TadoException: If device authentication is not completed
        """
        if self._api is None:
            if self._http.device_activation_status == DeviceActivationStatus.COMPLETED:
                if self._http.is_x_line:
                    self._api = API.TadoX.from_http(http=self._http, debug=self._debug)
                else:
                    self._api = API.Tado.from_http(http=self._http, debug=self._debug)
            else:
                raise TadoException(
                    "API is not initialized. Please complete device authentication first."
                )
