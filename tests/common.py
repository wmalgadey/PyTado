"""Common utils for tests."""

import os


def load_fixture(filename: str) -> str:
    """Load a fixture."""
    path = os.path.join(os.path.dirname(__file__), "fixtures", filename)
    with open(path) as fd:
        return fd.read()
