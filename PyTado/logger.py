"""
This file contains anything related to logging
"""

import logging


class Logger(logging.Logger):
    """
    This class provides a custom logger without masking sensitive information.
    """

    class SimpleFormatter(logging.Formatter):
        """
        Simple formatter that does not remove any information in logs.
        """

    def __init__(self, name: str, level=logging.NOTSET):
        super().__init__(name)
        log_sh = logging.StreamHandler()
        log_fmt = self.SimpleFormatter(fmt="%(name)s :: %(levelname)-8s :: %(message)s")
        log_sh.setFormatter(log_fmt)
        self.addHandler(log_sh)
        self.setLevel(level)
