"""
This file contains anything related to logging
"""

import logging
import re


class Logger(logging.Logger):
    """
    This class strips out sensitive information from logs
    """

    class SensitiveFormatter(logging.Formatter):
        """
        Formatter that removes sensitive information in logs.
        """

        @staticmethod
        def _filter(s):
            patterns = [
                r"'Bearer [\w-]*\.[\w-]*\.[\w-]*'",
                r"'access_token': '[\w-]*\.[\w-]*\.[\w-]*'",
                r"'refresh_token': '[\w-]*\.[\w-]*\.[\w-]*'",
                r"\?.*",
            ]
            try:
                for pattern in patterns:
                    s = re.sub(pattern, r"<MASKED>", s)
            except (KeyError, TypeError, ValueError):
                pass
            return s

        def format(self, record):
            """
            Do the actual filtering
            """
            original = logging.Formatter.format(
                self, record
            )  # call parent method
            return self._filter(original)

    def __init__(self, name: str, level=logging.NOTSET):
        super().__init__(name)
        log_sh = logging.StreamHandler()
        log_fmt = self.SensitiveFormatter(
            fmt="%(name)s :: %(levelname)-8s :: %(message)s"
        )
        log_sh.setFormatter(log_fmt)
        self.addHandler(log_sh)
