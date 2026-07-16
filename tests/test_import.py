"""Smoke tests for dash_upset packaging.

These verify the package is importable and correctly packaged. Behavioral
tests live in ``test_data.py`` and ``test_figure.py``.
"""

import dash_upset


def test_package_imports():
    assert dash_upset is not None


def test_version_is_defined():
    version = dash_upset.__version__
    assert isinstance(version, str)
    # Expect a semver-like "MAJOR.MINOR.PATCH".
    assert version.count(".") >= 2
