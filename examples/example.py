"""Example client for PyTado"""

from PyTado.interface.interface import authenticate_and_get_client


def main() -> None:
    """Retrieve all zones, once successfully logged in"""
    tado = authenticate_and_get_client()

    zones = tado.get_zones()
    print(zones)


if __name__ == "__main__":
    main()
