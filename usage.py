"""Local demo app for manual testing (like dash-seqviz's usage.py).

Run with ``pixi run python usage.py`` and click around: intersection bars and
matrix dots update ``selected_intersection``; set-size bars update
``selected_sets`` (ordinary component properties, read with the standard
``Input(id, property)`` convention). The third callback is the
drill-into-members cross-filter: it maps the selection back to the model's
stored element ids and lists them.
"""

from dash import Dash, Input, Output, callback, html

from dash_upset import UpSet, from_contents

# Element-level data (from_contents keeps each intersection's member ids), so a
# click can drill into exactly which elements the intersection contains.
contents = {
    "ResNet": ["img1", "img2", "img5", "img7", "img9"],
    "ViT": ["img2", "img5", "img8", "img9"],
    "XGBoost": ["img2", "img3", "img5", "img9"],
}
data = from_contents(contents)
members = {frozenset(i.sets): i.elements for i in data.intersections}

app = Dash(__name__)
app.layout = html.Div(
    [
        UpSet(
            id="errors",
            data=data,
            title="Model error sets",
            highlight_selection=True,
            selection_color="#d55e00",
        ),
        html.Pre(id="out-intersection", children="intersection: (click a bar or dot)"),
        html.Pre(id="out-sets", children="sets: (click a set-size bar)"),
        html.Pre(id="out-members", children="members: (click an intersection)"),
    ]
)


@callback(Output("out-intersection", "children"), Input("errors", "selected_intersection"))
def show_intersection(selection):
    return f"intersection: {selection}"


@callback(Output("out-sets", "children"), Input("errors", "selected_sets"))
def show_sets(selection):
    return f"sets: {selection}"


@callback(Output("out-members", "children"), Input("errors", "selected_intersection"))
def show_members(selection):
    if not selection:
        return "members: (click an intersection)"
    ids = members.get(frozenset(selection["sets"]), ())
    return f"members of {selection['label']}: {', '.join(map(str, ids))}"


if __name__ == "__main__":
    app.run(debug=False, port=8051)
