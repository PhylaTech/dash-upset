"""Local demo app for manual testing (like dash-seqviz's usage.py).

Run with ``pixi run python usage.py`` and click around: intersection bars and
matrix dots update ``selected_intersection``; set-size bars update
``selected_sets``. Both are ordinary component properties, read with the
standard ``Input(id, property)`` convention.
"""

import pandas as pd
from dash import Dash, Input, Output, callback, html

from dash_upset import UpSet

df = pd.DataFrame(
    {
        "Action": [1, 1, 0, 1, 0, 1, 1, 0],
        "Comedy": [1, 0, 1, 1, 0, 0, 1, 1],
        "Drama": [0, 1, 1, 1, 1, 0, 0, 1],
    }
)

app = Dash(__name__)
app.layout = html.Div(
    [
        UpSet(id="genes", data=df, sets=["Action", "Comedy", "Drama"], title="Movies"),
        html.Pre(id="out-intersection", children="intersection: (click a bar or dot)"),
        html.Pre(id="out-sets", children="sets: (click a set-size bar)"),
    ]
)


@callback(Output("out-intersection", "children"), Input("genes", "selected_intersection"))
def show_intersection(selection):
    return f"intersection: {selection}"


@callback(Output("out-sets", "children"), Input("genes", "selected_sets"))
def show_sets(selection):
    return f"sets: {selection}"


if __name__ == "__main__":
    app.run(debug=False, port=8051)
