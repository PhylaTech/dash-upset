"""Compiled Dash component package backing :class:`dash_upset.UpSet`.

This inner package holds the webpack-built plotly.js bundle and the
``dash-generate-components`` output for the ``DashUpset`` React component.
It is an implementation detail: import :class:`dash_upset.UpSet` instead of
using :class:`DashUpset` directly.

Regenerate with ``npm run build`` (see ``src/lib/`` and ``webpack.config.js``
at the repository root); the built artifacts are committed so installing and
packaging need no Node toolchain.
"""

import sys as _sys

import dash as _dash

from ._imports_ import *  # noqa: F403
from ._imports_ import __all__

# Dash appends this to served asset URLs (cache busting). Kept in lockstep
# with dash_upset.__version__ by release-please's extra-files updater.
__version__ = "0.1.1"  # x-release-please-version

if not hasattr(_dash, "development"):
    print(
        "Dash was not successfully imported. Make sure you don't have a file "
        'named \n"dash.py" in your current directory.',
        file=_sys.stderr,
    )
    _sys.exit(1)

_js_dist = [
    {
        "relative_package_path": "dash_upset_component.min.js",
        "namespace": "dash_upset_component",
    },
    {
        "relative_package_path": "dash_upset_component.min.js.map",
        "namespace": "dash_upset_component",
        "dynamic": True,
    },
]

_css_dist = []

for _component in __all__:
    _cls = globals()[_component]
    _cls._js_dist = _js_dist
    _cls._css_dist = _css_dist
