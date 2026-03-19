"""Minimal test: package is importable and version is defined."""

import re

from finops_buddy import __version__


def test_package_import():
    """Package can be imported and __version__ is set (from pyproject.toml via package metadata)."""
    assert isinstance(__version__, str), "__version__ must be a string"
    assert len(__version__) > 0, "__version__ must be non-empty"
    # Should look like a version (e.g. 0.1.4 or 0.0.0+dev)
    assert re.match(r"^\d+\.\d+\.\d+(\+\w+)?$", __version__), (
        f"__version__ should be semver-like, got {__version__!r}"
    )
