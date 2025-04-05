"""Example client for PyTado"""

from PyTado.interface.interface import Tado


def main() -> None:
    """Retrieve all zones, once successfully logged in"""
    tado = Tado()

    print("Device activation status: ", tado.device_activation_status())
    print("Device verification URL: ", tado.device_verification_url())

    print("Starting device activation")
    tado.device_activation()

    print("Device activation status: ", tado.device_activation_status())

    zones = tado.get_zones()
    print(zones)


if __name__ == "__main__":
    main()
