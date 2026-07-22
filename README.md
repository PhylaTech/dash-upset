# dash-upset

Interactive [UpSet plots](https://upset.app) for [Plotly Dash](https://dash.plotly.com).

> **Status: early development (pre-1.0).** The data model, the figure factory
> (`create_upset`), and the interactive `UpSet` Dash component with
> click-selection callback properties are implemented and tested; see the
> [roadmap](./ROADMAP.md) for what's next. Available from conda-forge and
> PyPI. Documentation: https://phylatech.github.io/dash-upset/

## What is an UpSet plot?

An UpSet plot visualizes the intersections of many sets. Venn and Euler
diagrams become unreadable past three or four sets; UpSet replaces the
overlapping circles with:

- a **matrix** whose columns are sets and whose rows are intersections (filled,
  connected dots show which sets participate in each intersection),
- **set-size bars** giving the cardinality of each individual set, and
- **intersection-size bars** giving the size of each intersection.

This scales to dozens of sets and makes the large intersections obvious at a
glance. `dash-upset` aims to bring this to Dash as a reusable, themeable,
callback-friendly component.

## Why this exists

There is no first-class UpSet component for Dash, and wrapping the existing
JavaScript implementations has real costs: [UpSet.js](https://upset.js.org) is
**AGPLv3** (unsuitable for a permissively licensed library), and while
[UpSet 2.0](https://github.com/visdesignlab/upset2) is BSD-3-Clause, embedding
its React stack would drag a heavy dependency tree into every app and give up
notebook rendering and static export.

`dash-upset` therefore keeps all UpSet logic (data model, modes, sorting,
filtering, deviation, theming) in pure Python, composing the figure from
Plotly primitives: MIT-clean and notebook-friendly. The `UpSet` component adds
a thin compiled React layer (react-plotly.js) on top of that same figure so
clicks surface as ordinary Dash component properties; the build artifacts are
committed, so installing and using the package needs no Node toolchain.
`upset2-react` remains the documented fallback engine if Plotly's interaction
ceiling is ever reached. See the [roadmap](./ROADMAP.md) for the full analysis
and the decision record.

## Installation

`dash-upset` is not published yet. Once released:

```bash
# conda-forge (preferred)
conda install -c conda-forge dash-upset

# or pip
pip install dash-upset
```

## Quick start

Drop the `UpSet` component into a Dash layout with a dataframe of boolean
indicator columns (one per set). Clicks surface as component properties your
callbacks read the standard Dash way:

```python
import pandas as pd
from dash import Dash, Input, Output, callback, html
from dash_upset import UpSet

# One row per misclassified test example; 1 = that model got it wrong.
# Overlaps are the shared hard cases; singletons are each model's blind spots.
df = pd.DataFrame(
    {
        "ResNet": [1, 1, 0, 1, 0, 1],
        "ViT": [1, 1, 1, 0, 0, 1],
        "XGBoost": [0, 1, 1, 1, 1, 0],
    }
)

app = Dash(__name__)
app.layout = html.Div(
    [
        UpSet(id="errors", data=df, sets=["ResNet", "ViT", "XGBoost"]),
        html.Pre(id="out"),
    ]
)


@callback(Output("out", "children"), Input("errors", "selected_intersection"))
def show(selection):
    # {"label": "ResNet & ViT", "sets": ["ResNet", "ViT"], "size": 2}
    return str(selection)


if __name__ == "__main__":
    app.run(debug=True)
```

`selected_intersection` updates when an intersection-size bar or a matrix dot
is clicked; `selected_sets` (a list of set names) updates when a set-size bar
is clicked.

### Just the figure

For notebooks, scripts, or static export, `create_upset` takes the same input
and returns a plain `plotly.graph_objects.Figure`:

```python
from dash_upset import create_upset, from_counts

fig = create_upset(
    from_counts({
        "Action": 320, "Comedy": 290, "Drama": 410,
        "Action&Comedy": 84, "Action&Drama": 120, "Comedy&Drama": 96,
        "Action&Comedy&Drama": 40,
    }),
    title="Movie genres",
)
fig.show()
```

Element-level data uses the familiar
[`upsetplot`](https://upsetplot.readthedocs.io) conventions:

```python
from dash_upset import from_contents, from_indicators, from_memberships

from_memberships([("A",), ("A", "B"), ()])          # per-element set names
from_contents({"A": ["x", "y"], "B": ["y", "z"]})   # per-set element ids
from_indicators(boolean_dataframe)                  # rows = elements, columns = sets
```

`from_indicators` is dataframe-agnostic via
[narwhals](https://github.com/narwhals-dev/narwhals): pandas, Polars, PyArrow,
cuDF, and Modin frames (or a plain dict of boolean columns) all work, and
`dash-upset` itself depends on none of those libraries.

Sorting and display are controlled per plot, e.g.
`UpSet(data=df, sets=[...], sort_by="degree", sort_sets_by="name", theme="dark")`;
`create_upset` accepts the same keywords. The full argument reference lives at
https://phylatech.github.io/dash-upset/reference.html.

## Development

This project uses [pixi](https://pixi.sh) for environment and task management.

```bash
pixi install          # create the environment (deps from conda-forge)
pixi run test         # run the test suite
pixi run lint         # ruff lint
pixi run format       # ruff format
```

The compiled React layer behind the `UpSet` component
(`dash_upset_component/`) is committed, so none of the above needs Node. To
change it, edit `src/lib/components/DashUpset.react.js` and rebuild:

```bash
npm install
pixi run build-component   # webpack bundle + dash-generate-components classes
```

See [CONTRIBUTING.md](./CONTRIBUTING.md) for the commit conventions that drive
releases.

## Prior art and credits

- [UpSet](https://upset.app) and the original research by Lex, Gehlenborg,
  et al. define the technique.
- [UpSet 2.0](https://github.com/visdesignlab/upset2) by the Visualization
  Design Lab (BSD-3-Clause) is the technique authors' interactive
  reimplementation and the documented candidate engine should this library
  ever add a JavaScript renderer (see the roadmap).
- [UpSet.js](https://upset.js.org) by Samuel Gratzl is an interactive JS
  implementation (AGPLv3 / commercial).
- [`upsetplot`](https://upsetplot.readthedocs.io) by Joel Nothman (BSD-3-Clause)
  is the established matplotlib-based Python package; `dash-upset` mirrors its
  familiar data-input conventions.

## License

[MIT](./LICENSE) © Evan Roy Rees
