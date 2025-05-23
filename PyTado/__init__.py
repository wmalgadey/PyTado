from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("python-tado")
except PackageNotFoundError:
    __version__ = "test"  # happens when running as pre-commit hook
