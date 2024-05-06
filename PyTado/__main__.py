#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Module for querying and controlling Tado smart thermostats."""

import argparse
import logging
import sys

from PyTado.interface import Tado


def log_in(email, password):
    t = Tado(email, password)
    return t


def get_me(args):
    t = Tado(args.email, args.password)
    me = t.get_me()
    print(me)


def get_state(args):
    t = Tado(args.email, args.password)
    zone = t.get_state(int(args.zone))
    print(zone)


def get_states(args):
    t = Tado(args.email, args.password)
    zone = t.get_zone_states()
    print(zone)


def get_capabilities(args):
    t = Tado(args.email, args.password)
    capabilities = t.get_capabilities(int(args.zone))
    print(capabilities)


def main():
    """Main method for the script."""
    parser = argparse.ArgumentParser(
        description="Pytado - Tado thermostat device control",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    required_flags = parser.add_argument_group("required arguments")

    # Required flags go here.
    required_flags.add_argument(
        "--email",
        required=True,
        help=("Tado username in the form of an email address."),
    )
    required_flags.add_argument(
        "--password", required=True, help="Tado password."
    )

    # Flags with default values go here.
    log_levels = dict(
        (logging.getLevelName(level), level) for level in [10, 20, 30, 40, 50]
    )
    parser.add_argument(
        "--loglevel",
        default="INFO",
        choices=list(log_levels.keys()),
        help="Logging level to print to the console.",
    )

    subparsers = parser.add_subparsers()

    show_config_parser = subparsers.add_parser(
        "get_me", help="Get home information."
    )
    show_config_parser.set_defaults(func=get_me)

    start_activity_parser = subparsers.add_parser(
        "get_state", help="Get state of zone."
    )
    start_activity_parser.add_argument(
        "--zone", help="Zone to get the state of."
    )
    start_activity_parser.set_defaults(func=get_state)

    start_activity_parser = subparsers.add_parser(
        "get_states", help="Get states of all zones."
    )
    start_activity_parser.set_defaults(func=get_states)

    start_activity_parser = subparsers.add_parser(
        "get_capabilities", help="Get capabilities of zone."
    )
    start_activity_parser.add_argument(
        "--zone", help="Zone to get the capabilities of."
    )
    start_activity_parser.set_defaults(func=get_capabilities)

    args = parser.parse_args()

    logging.basicConfig(
        level=log_levels[args.loglevel],
        format="%(levelname)s:\t%(name)s\t%(message)s",
    )

    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
