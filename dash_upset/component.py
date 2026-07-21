"""The self-wiring ``UpSet`` Dash All-in-One component.

``UpSet`` is the Dash-native entry point: a component you drop into a layout
(like ``dcc.Graph`` or the sibling ``SeqViz``), not a figure. It wraps
:func:`~dash_upset.figure.create_upset` in a ``dcc.Graph`` and registers a
pattern-matching callback so clicks become selection state, exposed on two
stores your own callbacks can read::

    from dash import Dash, html, Input, Output, callback
    from dash_upset import UpSet

    app = Dash(__name__)
    app.layout = html.Div([
        UpSet(id="genes", data=df, sets=["A", "B", "C"]),
        html.Pre(id="out"),
    ])

    @callback(Output("out", "children"), Input(UpSet.ids.selected_intersection("genes"), "data"))
    def show(selection):
        return str(selection)

For notebooks, static export, or embedding a bare figure, use
:func:`~dash_upset.figure.create_upset` directly -- ``UpSet`` renders the same
figure and adds the interactive wiring on top.
"""

from __future__ import annotations

import uuid

from dash import MATCH, Input, Output, State, callback, dcc, html, no_update

from .figure import create_upset

__all__ = ["UpSet"]


def _selection_from_click(figure: dict, click: dict | None):
    """Map a Plotly ``clickData`` payload to (intersection, sets) selection.

    Pure and side-effect-free so it can be unit-tested without a Dash server.
    Returns a 2-tuple; ``dash.no_update`` for the output a given click does not
    change. The clicked trace is identified by its stable ``meta`` id, looked
    up in the figure by ``curveNumber``.
    """
    if not click or not click.get("points"):
        return no_update, no_update
    point = click["points"][0]
    try:
        meta = figure["data"][point["curveNumber"]].get("meta")
    except (KeyError, IndexError, TypeError):
        meta = None
    customdata = point.get("customdata") or []

    if meta == "upset:intersection-bars":
        label = customdata[0] if customdata else None
        member_sets = label.split(" & ") if label and label != "(no sets)" else []
        return {"label": label, "sets": member_sets, "size": point.get("y")}, no_update

    if meta == "upset:matrix-dots":
        # customdata is [set_name, "A & B (size)"]; recover the label.
        label = customdata[1].rsplit(" (", 1)[0] if len(customdata) > 1 else None
        member_sets = label.split(" & ") if label and label != "(no sets)" else []
        return {"label": label, "sets": member_sets}, no_update

    if meta == "upset:set-bars":
        name = customdata[0] if customdata else None
        return no_update, ([name] if name else no_update)

    return no_update, no_update


class UpSet(html.Div):
    """A self-wiring UpSet component for a Dash layout.

    Args:
        data: A dataframe / mapping of boolean indicator columns, or an
            :class:`~dash_upset.data.UpSetData`. Same as
            :func:`~dash_upset.figure.create_upset`.
        sets: Columns to treat as sets when ``data`` is a dataframe.
        id: The All-in-One id used to address this component's parts from
            callbacks (via ``UpSet.ids.*``). Defaults to a random uuid.
        graph_config: Optional ``dcc.Graph`` ``config`` override.
        **kwargs: Forwarded to ``create_upset`` (``mode``, ``sort_by``,
            ``theme``, filtering, ...).

    Selection is exposed on two stores addressable via the ``ids`` factories:
    ``UpSet.ids.selected_intersection(id)`` (``{"label", "sets", "size"}`` when
    an intersection bar or matrix dot is clicked) and
    ``UpSet.ids.selected_sets(id)`` (a list of set names when a set-size bar is
    clicked).
    """

    class ids:
        @staticmethod
        def graph(aio_id: str) -> dict:
            return {"component": "UpSet", "subcomponent": "graph", "aio_id": aio_id}

        @staticmethod
        def selected_intersection(aio_id: str) -> dict:
            return {"component": "UpSet", "subcomponent": "selected_intersection", "aio_id": aio_id}

        @staticmethod
        def selected_sets(aio_id: str) -> dict:
            return {"component": "UpSet", "subcomponent": "selected_sets", "aio_id": aio_id}

    def __init__(self, data, sets=None, id=None, graph_config=None, **kwargs):
        aio_id = id if id is not None else str(uuid.uuid4())
        figure = create_upset(data, sets=sets, **kwargs)
        super().__init__(
            [
                dcc.Graph(
                    id=self.ids.graph(aio_id),
                    figure=figure,
                    config=graph_config or {"displayModeBar": False},
                ),
                dcc.Store(id=self.ids.selected_intersection(aio_id)),
                dcc.Store(id=self.ids.selected_sets(aio_id)),
            ]
        )


@callback(
    Output(UpSet.ids.selected_intersection(MATCH), "data"),
    Output(UpSet.ids.selected_sets(MATCH), "data"),
    Input(UpSet.ids.graph(MATCH), "clickData"),
    State(UpSet.ids.graph(MATCH), "figure"),
    prevent_initial_call=True,
)
def _upset_on_click(click, figure):
    return _selection_from_click(figure, click)
