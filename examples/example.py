"""Example client for PyTado"""

import os
import sys

from PyTado.interface.interface import Tado

tado_username = os.getenv("TADO_USERNAME", "")
tado_password = os.getenv("TADO_PASSWORD", "")

if len(tado_username) == 0 or len(tado_password) == 0:
    sys.exit("TADO_USERNAME and TADO_PASSWORD must be set")


def main() -> None:
    """Retrieve all zones, once successfully logged in"""
    tado = Tado(username=tado_username, password=tado_password)  # nosec
    zones = tado.get_zones()
    print(zones)


if __name__ == "__main__":
    main()
