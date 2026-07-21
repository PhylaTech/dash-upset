# AUTO GENERATED FILE - DO NOT EDIT

import typing  # noqa: F401
from typing_extensions import TypedDict, NotRequired, Literal # noqa: F401
from dash.development.base_component import Component, _explicitize_args
try:
    from dash.types import NumberType  # noqa: F401
except ImportError:
    # Backwards compatibility for dash<=4.1.0
    if typing.TYPE_CHECKING:
        raise
    NumberType = typing.Union[  # noqa: F401
        typing.SupportsFloat, typing.SupportsInt, typing.SupportsComplex
    ]

ComponentSingleType = typing.Union[str, int, float, Component, None]
ComponentType = typing.Union[
    ComponentSingleType,
    typing.Sequence[ComponentSingleType],
]


class DashUpset(Component):
    """A DashUpset component.
DashUpset renders an UpSet figure (built in Python by create_upset) with
plotly.js and turns clicks into two declared, callback-addressable props:
selected_intersection and selected_sets. It is the compiled component behind
dash_upset.UpSet; application code should construct it through UpSet(...),
which builds the figure for you.

The clicked trace is identified by its stable meta id:
"upset:intersection-bars" and "upset:matrix-dots" update selected_intersection;
"upset:set-bars" updates selected_sets. Clicks elsewhere are ignored.

Keyword arguments:

- id (string; optional):
    The ID used to identify this component in Dash callbacks.

- className (string; optional):
    CSS class name for the outer container div.

- config (dict; default {displayModeBar: False, responsive: True}):
    The plotly.js config object for the graph (mode bar,
    responsiveness, ...).

- figure (dict; default {data: [], layout: {}}):
    The Plotly figure to render, as produced by
    dash_upset.create_upset (a dict with \"data\" and \"layout\").
    UpSet(...) sets this for you.

- selected_intersection (dict; optional):
    The currently selected intersection, set when an intersection-size
    bar or a matrix dot is clicked. An object {label, sets, size}
    (size is present only for bar clicks); None before any click.
    Read-only from callbacks.

- selected_sets (list; optional):
    The currently selected set(s), set when a set-size bar is clicked:
    a list of set names. Read-only from callbacks."""
    _children_props: typing.List[str] = []
    _base_nodes = ['children']
    _namespace = 'dash_upset_component'
    _type = 'DashUpset'


    def __init__(
        self,
        id: typing.Optional[typing.Union[str, dict]] = None,
        figure: typing.Optional[dict] = None,
        config: typing.Optional[dict] = None,
        selected_intersection: typing.Optional[dict] = None,
        selected_sets: typing.Optional[typing.Sequence] = None,
        style: typing.Optional[typing.Any] = None,
        className: typing.Optional[str] = None,
        **kwargs
    ):
        self._prop_names = ['id', 'className', 'config', 'figure', 'selected_intersection', 'selected_sets', 'style']
        self._valid_wildcard_attributes =            []
        self.available_properties = ['id', 'className', 'config', 'figure', 'selected_intersection', 'selected_sets', 'style']
        self.available_wildcard_properties =            []
        _explicit_args = kwargs.pop('_explicit_args')
        _locals = locals()
        _locals.update(kwargs)  # For wildcard attrs and excess named props
        args = {k: _locals[k] for k in _explicit_args}

        super(DashUpset, self).__init__(**args)

setattr(DashUpset, "__init__", _explicitize_args(DashUpset.__init__))
