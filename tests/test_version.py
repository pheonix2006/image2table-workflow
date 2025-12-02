"""Test version information."""

import pytest
from table2image_agent import __version__


def test_version_exists():
    """Test that __version__ is defined."""
    assert __version__ is not None


def test_version_format():
    """Test that version follows semantic versioning."""
    assert isinstance(__version__, str)
    # Simple semantic version pattern (major.minor.patch)
    import re
    version_pattern = r'^\d+\.\d+\.\d+$'
    assert re.match(version_pattern, __version__), f"Version '{__version__}' doesn't follow semantic versioning"


def test_version_value():
    """Test that version is 0.1.0."""
    assert __version__ == "0.1.0"