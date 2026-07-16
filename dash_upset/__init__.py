"""dash-upset: interactive UpSet plots for Plotly Dash.

UpSet plots visualize the intersections of many sets, where Venn diagrams break
down past three or four sets. See https://upset.app for the technique and
``ROADMAP.md`` in this repository for the design plan.

The M1 API builds a data model with one of the ``from_*`` constructors and
renders it with :func:`create_upset`::

    from dash_upset import create_upset, from_counts

    fig = create_upset(from_counts({"A": 10, "B": 4, "A&B": 6}))
    fig.show()  # or dcc.Graph(figure=fig) inside a Dash layout

The self-wiring ``UpSet(...)`` Dash component (click selection, callback
outputs) arrives in M2; see the roadmap.
"""

from .data import (
    UpSetData,
    UpSetIntersection,
    from_contents,
    from_counts,
    from_indicators,
    from_memberships,
)
from .figure import create_upset

__version__ = "0.1.0"

__all__ = [
    "UpSetData",
    "UpSetIntersection",
    "create_upset",
    "from_contents",
    "from_counts",
    "from_indicators",
    "from_memberships",
]
