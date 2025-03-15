#!/usr/bin/env python3

"""Module for querying and controlling Tado smart thermostats."""

import argparse
import logging
import sys

from PyTado.interface import Tado


def log_in(args):
    """
    Log in to the Tado API by activating the current device.

    Add --token_file_path to the command line arguments to store the
    refresh token in a file.

    Args:
        args (argparse.Namespace): The parsed command-line arguments.

    Returns:
        Tado: An instance of the Tado interface.
    """
    t = Tado(token_file_path=args.token_file_path)
    t.device_activation()
    return t


def get_me(args):
    """
    Retrieve and print home information from the Tado API.

    Args:
        args (argparse.Namespace): The parsed command-line arguments.
    """
    t = log_in(args)
    me = t.get_me()
    print(me)


def get_state(args):
    """
    Retrieve and print the state of a specific zone from the Tado API.

    Args:
        args (argparse.Namespace): The parsed command-line arguments.
    """
    t = log_in(args)
    zone = t.get_state(int(args.zone))
    print(zone)


def get_states(args):
    """
    Retrieve and print the states of all zones from the Tado API.

    Args:
        args (argparse.Namespace): The parsed command-line arguments.
    """
    t = log_in(args)
    zones = t.get_zone_states()
    print(zones)


def get_capabilities(args):
    """
    Retrieve and print the capabilities of a specific zone from the Tado API.

    Args:
        args (argparse.Namespace): The parsed command-line arguments.
    """
    t = log_in(args)
    capabilities = t.get_capabilities(int(args.zone))
    print(capabilities)


def main():
    """
    Main method for the script.

    Sets up the argument parser, handles subcommands, and executes the appropriate function.
    """
    parser = argparse.ArgumentParser(
        description="Pytado - Tado thermostat device control",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    required_flags = parser.add_argument_group("required arguments")

    # Required flags go here.
    required_flags.add_argument(
        "--token_file_path",
        required=True,
        help="Path to the file where the refresh token should be stored.",
    )

    # Flags with default values go here.
    log_levels = {logging.getLevelName(level): level for level in [10, 20, 30, 40, 50]}
    parser.add_argument(
        "--loglevel",
        default="INFO",
        choices=list(log_levels.keys()),
        help="Logging level to print to the console.",
    )

    subparsers = parser.add_subparsers()

    show_config_parser = subparsers.add_parser("get_me", help="Get home information.")
    show_config_parser.set_defaults(func=get_me)

    start_activity_parser = subparsers.add_parser("get_state", help="Get state of zone.")
    start_activity_parser.add_argument("--zone", help="Zone to get the state of.")
    start_activity_parser.set_defaults(func=get_state)

    start_activity_parser = subparsers.add_parser("get_states", help="Get states of all zones.")
    start_activity_parser.set_defaults(func=get_states)

    start_activity_parser = subparsers.add_parser(
        "get_capabilities", help="Get capabilities of zone."
    )
    start_activity_parser.add_argument("--zone", help="Zone to get the capabilities of.")
    start_activity_parser.set_defaults(func=get_capabilities)

    args = parser.parse_args()

    logging.basicConfig(
        level=log_levels[args.loglevel],
        format="%(levelname)s:\t%(name)s\t%(message)s",
    )

    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
