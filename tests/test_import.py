"""Smoke tests for the dash_upset package skeleton.

These verify the package is importable and correctly packaged. Behavioral tests
for the UpSet API arrive with the implementation phase (see ROADMAP.md).
"""

import dash_upset


def test_package_imports():
    assert dash_upset is not None


def test_version_is_defined():
    version = dash_upset.__version__
    assert isinstance(version, str)
    # Expect a semver-like "MAJOR.MINOR.PATCH".
    assert version.count(".") >= 2
