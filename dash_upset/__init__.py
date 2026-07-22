"""dash-upset: interactive UpSet plots for Plotly Dash.

UpSet plots visualize the intersections of many sets, where Venn diagrams break
down past three or four sets. See https://upset.app for the technique and
``ROADMAP.md`` in this repository for the design plan.

Two entry points, mirroring the Plotly/Dash split:

- ``UpSet`` -- a self-wiring Dash component (PascalCase, like ``dcc.Graph`` /
  ``SeqViz``) that goes in a layout and exposes click selection to callbacks::

      from dash import Dash
      from dash_upset import UpSet

      app = Dash(__name__)
      app.layout = UpSet(id="genes", data=df, sets=["A", "B", "C"])

- ``create_upset`` -- the figure factory beneath it (lowercase, like
  ``plotly.figure_factory.create_*``), returning a ``go.Figure`` for notebooks,
  static export, or ``dcc.Graph``::

      from dash_upset import create_upset

      fig = create_upset(df, sets=["A", "B", "C"])
      fig.show()

Both take a dataframe of boolean indicator columns directly (the Plotly-style
input); the ``from_*`` constructors remain for pre-aggregated counts, set
contents, or per-element memberships.
"""

from .component import UpSet
from .data import (
    UpSetData,
    UpSetIntersection,
    from_contents,
    from_counts,
    from_indicators,
    from_memberships,
)
from .figure import create_upset

__version__ = "0.1.1"

__all__ = [
    "UpSet",
    "UpSetData",
    "UpSetIntersection",
    "create_upset",
    "from_contents",
    "from_counts",
    "from_indicators",
    "from_memberships",
]
