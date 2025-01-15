"""Tests for Python Tado."""
from pathlib import Path


def load_fixture(filename: str, folder: str = "") -> str:
    """Load a fixture."""
    if folder:
        path = Path(__package__) / "fixtures" / folder / filename
    else:
        path = Path(__package__) / "fixtures" / filename
    return path.read_text(encoding="utf-8")
