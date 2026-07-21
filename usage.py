"""Local demo app for manual testing (like dash-seqviz's usage.py).

Run with ``pixi run python usage.py`` and click around: intersection bars and
matrix dots update ``selected_intersection``; set-size bars update
``selected_sets``. Both are ordinary component properties, read with the
standard ``Input(id, property)`` convention.
"""

import pandas as pd
from dash import Dash, Input, Output, callback, html

from dash_upset import UpSet

# One row per misclassified test example; 1 = that model got it wrong.
df = pd.DataFrame(
    {
        "ResNet": [1, 1, 0, 1, 0, 1, 1, 0],
        "ViT": [1, 0, 1, 1, 0, 0, 1, 1],
        "XGBoost": [0, 1, 1, 1, 1, 0, 0, 1],
    }
)

app = Dash(__name__)
app.layout = html.Div(
    [
        UpSet(
            id="errors",
            data=df,
            sets=["ResNet", "ViT", "XGBoost"],
            title="Model error sets",
            highlight_selection=True,
            selection_color="#d55e00",
        ),
        html.Pre(id="out-intersection", children="intersection: (click a bar or dot)"),
        html.Pre(id="out-sets", children="sets: (click a set-size bar)"),
    ]
)


@callback(Output("out-intersection", "children"), Input("errors", "selected_intersection"))
def show_intersection(selection):
    return f"intersection: {selection}"


@callback(Output("out-sets", "children"), Input("errors", "selected_sets"))
def show_sets(selection):
    return f"sets: {selection}"


if __name__ == "__main__":
    app.run(debug=False, port=8051)
