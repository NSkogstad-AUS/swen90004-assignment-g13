"""Top-level unittest bridge for the Hotelling model test suite."""

import sys
import unittest
from pathlib import Path
from typing import Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HOTELLING_ROOT = PROJECT_ROOT / "hotelling-law"
HOTELLING_TESTS = HOTELLING_ROOT / "tests"


def load_tests(
    loader: unittest.TestLoader,
    tests: unittest.TestSuite,
    pattern: Optional[str],
) -> unittest.TestSuite:
    """Let root-level discovery run the nested Hotelling test suite."""
    sys.path.insert(0, str(HOTELLING_ROOT))
    nested_loader = unittest.TestLoader()
    return nested_loader.discover(str(HOTELLING_TESTS), pattern=pattern or "test*.py")
