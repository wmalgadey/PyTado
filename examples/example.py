"""Example client for PyTado"""

from PyTado.interface.interface import Tado


def main() -> None:
    """Retrieve all zones, once successfully logged in"""
    tado = Tado(username="mail@email.com", password="password")  # nosec
    zones = tado.get_zones()
    print(zones)


if __name__ == "__main__":
    main()
