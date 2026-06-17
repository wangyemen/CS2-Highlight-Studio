"""
Core package
"""
import sys
from pathlib import Path


def get_app_root():
    """Get application root directory.
    When frozen (packaged), return the
    directory containing the executable.
    When running from source, return the
    project root."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent.parent
    return Path(__file__).parent.parent