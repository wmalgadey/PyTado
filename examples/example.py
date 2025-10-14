"""Example client for PyTado"""

from PyTado.factory import TadoClientInitializer


def main() -> None:
    """Retrieve all zones, once successfully logged in"""
    tado = TadoClientInitializer().authenticate_and_get_client()

    zones = tado.get_zones()

    print(zones)


if __name__ == "__main__":
    main()
