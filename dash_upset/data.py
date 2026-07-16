"""Data model for UpSet plots.

The constructors mirror the input conventions of the BSD-licensed ``upsetplot``
package (``from_memberships``, ``from_contents``, ``from_indicators``) plus a
``from_counts`` convenience for pre-aggregated data. All of them normalize to
the canonical :class:`UpSetData` model that the renderer consumes:

- an ordered list of set names with their total sizes, and
- an ordered list of exclusive intersections (``degree``, ``sets``, ``size``,
  and, when the input carries them, the member ``elements``).

Intersections are *exclusive* ("distinct" in UpSet terminology): an element
belonging to exactly sets A and B counts toward the ``(A, B)`` intersection
only, not toward ``(A,)`` or ``(B,)``. Set totals always refer to the full set
size, so they equal the sum of the sizes of every intersection that contains
the set.
"""

from __future__ import annotations

import math
from collections.abc import Hashable, Iterable, Mapping, Sequence
from dataclasses import dataclass

import pandas as pd

__all__ = [
    "UpSetData",
    "UpSetIntersection",
    "from_contents",
    "from_counts",
    "from_indicators",
    "from_memberships",
    "sort_intersections",
    "sort_sets",
]


@dataclass(frozen=True)
class UpSetIntersection:
    """One exclusive intersection: the elements in exactly ``sets``, no others.

    Attributes:
        sets: The member set names, ordered consistently with the parent
            :class:`UpSetData.set_names`. Empty for the "in no set" group.
        size: The size of the intersection (a count, or a pre-aggregated
            value when built with :func:`from_counts`).
        elements: The ids of the member elements, when the input provided
            them; ``None`` for pre-aggregated data.
    """

    sets: tuple[str, ...]
    size: float
    elements: tuple[Hashable, ...] | None = None

    def __post_init__(self) -> None:
        if len(set(self.sets)) != len(self.sets):
            raise ValueError(f"intersection has duplicate set names: {self.sets!r}")
        if self.size < 0:
            raise ValueError(f"intersection size must be >= 0, got {self.size!r}")
        if self.elements is not None and len(self.elements) != self.size:
            raise ValueError(
                f"intersection of {self.sets!r} has size {self.size!r} but "
                f"{len(self.elements)} elements"
            )

    @property
    def degree(self) -> int:
        """The number of sets participating in this intersection."""
        return len(self.sets)


@dataclass(frozen=True)
class UpSetData:
    """The canonical UpSet model: ordered sets plus exclusive intersections.

    Instances are normally built with one of the ``from_*`` constructors
    rather than directly. ``set_names`` and ``set_sizes`` are aligned;
    ``set_sizes`` are the *total* set sizes, independent of any filtering a
    renderer may later apply to the intersections.
    """

    set_names: tuple[str, ...]
    set_sizes: tuple[float, ...]
    intersections: tuple[UpSetIntersection, ...]

    def __post_init__(self) -> None:
        if len(self.set_names) != len(self.set_sizes):
            raise ValueError(
                f"got {len(self.set_names)} set names but {len(self.set_sizes)} set sizes"
            )
        for name in self.set_names:
            if not isinstance(name, str) or not name:
                raise ValueError(f"set names must be non-empty strings, got {name!r}")
        if len(set(self.set_names)) != len(self.set_names):
            raise ValueError(f"duplicate set names: {self.set_names!r}")
        for size in self.set_sizes:
            if size < 0:
                raise ValueError(f"set sizes must be >= 0, got {size!r}")
        known = set(self.set_names)
        for intersection in self.intersections:
            unknown = [name for name in intersection.sets if name not in known]
            if unknown:
                raise ValueError(
                    f"intersection {intersection.sets!r} references unknown sets: {unknown!r}"
                )

    @property
    def total_size(self) -> float:
        """The combined size of all intersections (i.e. all elements)."""
        return sum(intersection.size for intersection in self.intersections)

    def set_size(self, name: str) -> float:
        """The total size of the set called ``name``."""
        try:
            return self.set_sizes[self.set_names.index(name)]
        except ValueError:
            raise KeyError(name) from None


def _validated_membership(names: Iterable[str], where: str) -> list[str]:
    """Validate one element's collection of set names."""
    if isinstance(names, (str, bytes)):
        raise TypeError(
            f"{where} must be a collection of set names, got the string {names!r} "
            "(a bare string would be treated as its characters)"
        )
    result = list(names)
    seen: set[str] = set()
    for name in result:
        if not isinstance(name, str) or not name:
            raise ValueError(f"{where} contains an invalid set name: {name!r}")
        if name in seen:
            raise ValueError(f"{where} lists the set {name!r} more than once")
        seen.add(name)
    return result


def _build(
    set_order: Sequence[str],
    per_element: Iterable[tuple[Hashable, Sequence[str]]],
) -> UpSetData:
    """Assemble an UpSetData from per-element memberships (already validated)."""
    index = {name: position for position, name in enumerate(set_order)}
    combos: dict[frozenset, list[Hashable]] = {}
    set_counts = dict.fromkeys(set_order, 0)
    for element, names in per_element:
        combos.setdefault(frozenset(names), []).append(element)
        for name in names:
            set_counts[name] += 1
    intersections = tuple(
        UpSetIntersection(
            sets=tuple(sorted(combo, key=index.__getitem__)),
            size=len(elements),
            elements=tuple(elements),
        )
        for combo, elements in combos.items()
    )
    return UpSetData(
        set_names=tuple(set_order),
        set_sizes=tuple(set_counts[name] for name in set_order),
        intersections=intersections,
    )


def from_memberships(
    memberships: Iterable[Iterable[str]],
    element_ids: Sequence[Hashable] | None = None,
) -> UpSetData:
    """Build the model from one collection of set names per element.

    Args:
        memberships: For each element, the names of the sets it belongs to
            (an empty collection means the element is in no set). Set display
            order follows first appearance.
        element_ids: Optional ids for the elements, same length and order as
            ``memberships``. Defaults to positional indices.

    Example:
        >>> from_memberships([("A",), ("A", "B"), ()])  # doctest: +SKIP
    """
    parsed = [
        _validated_membership(membership, f"memberships[{position}]")
        for position, membership in enumerate(memberships)
    ]
    if element_ids is None:
        ids: Sequence[Hashable] = range(len(parsed))
    else:
        ids = list(element_ids)
        if len(ids) != len(parsed):
            raise ValueError(f"got {len(parsed)} memberships but {len(ids)} element_ids")
    set_order: dict[str, None] = {}
    for names in parsed:
        for name in names:
            set_order.setdefault(name)
    return _build(list(set_order), zip(ids, parsed))


def from_contents(contents: Mapping[str, Iterable[Hashable]]) -> UpSetData:
    """Build the model from ``{set_name: iterable_of_element_ids}``.

    Elements listed more than once in the same set are counted once. Set
    display order follows the mapping order; element order follows first
    appearance across sets.

    Example:
        >>> from_contents({"A": ["x", "y"], "B": ["y", "z"]})  # doctest: +SKIP
    """
    set_order: list[str] = []
    membership: dict[Hashable, list[str]] = {}
    for name, elements in contents.items():
        if not isinstance(name, str) or not name:
            raise ValueError(f"set names must be non-empty strings, got {name!r}")
        if name in set_order:
            raise ValueError(f"duplicate set name: {name!r}")
        if isinstance(elements, (str, bytes)):
            raise TypeError(
                f"contents[{name!r}] must be a collection of element ids, got the "
                f"string {elements!r} (a bare string would be treated as its characters)"
            )
        set_order.append(name)
        for element in elements:
            names = membership.setdefault(element, [])
            if name not in names:
                names.append(name)
    return _build(set_order, membership.items())


def from_indicators(
    indicators: pd.DataFrame | Mapping[str, Sequence[bool]],
) -> UpSetData:
    """Build the model from a boolean indicator table (rows = elements).

    Args:
        indicators: A DataFrame (or mapping of columns) whose columns are set
            names and whose values are booleans (or 0/1 integers) marking
            membership. The index provides the element ids.

    Example:
        >>> from_indicators(pd.DataFrame({"A": [True, False]}))  # doctest: +SKIP
    """
    if isinstance(indicators, pd.DataFrame):
        frame = indicators
    elif isinstance(indicators, Mapping):
        frame = pd.DataFrame(dict(indicators))
    else:
        raise TypeError(
            "indicators must be a pandas DataFrame or a mapping of column "
            f"name to boolean values, got {type(indicators).__name__}"
        )
    set_order: list[str] = []
    for column in frame.columns:
        if not isinstance(column, str) or not column:
            raise ValueError(
                f"indicator column names are used as set names and must be "
                f"non-empty strings, got {column!r}"
            )
        series = frame[column]
        if series.isna().any():
            raise ValueError(f"indicator column {column!r} contains missing values")
        is_boolean = pd.api.types.is_bool_dtype(series)
        is_zero_one = pd.api.types.is_integer_dtype(series) and series.isin((0, 1)).all()
        if not (is_boolean or is_zero_one):
            raise ValueError(
                f"indicator column {column!r} must be boolean (or 0/1 integers), "
                f"got dtype {series.dtype}"
            )
        set_order.append(column)
    matrix = frame.astype(bool).to_numpy()
    per_element = (
        (element, [name for name, member in zip(set_order, row) if member])
        for element, row in zip(frame.index.tolist(), matrix)
    )
    return _build(set_order, per_element)


def from_counts(
    counts: Mapping[str | tuple[str, ...], float],
    sep: str = "&",
) -> UpSetData:
    """Build the model from pre-aggregated exclusive intersection sizes.

    Args:
        counts: A mapping from intersection to size. Keys are either tuples of
            set names or strings joined with ``sep`` (``"Action&Drama"``,
            whitespace around the separator is ignored). The empty tuple or
            empty string denotes elements belonging to no set. Sizes are the
            *exclusive* ("distinct") intersection sizes; set totals are
            derived by summing them.
        sep: The separator used to split string keys. Use tuple keys instead
            if your set names contain the separator.

    Example:
        >>> from_counts({"A": 10, "B": 4, "A&B": 6})  # doctest: +SKIP
    """
    set_order: dict[str, None] = {}
    parsed: list[tuple[tuple[str, ...], float]] = []
    seen: dict[frozenset, object] = {}
    for key, size in counts.items():
        if isinstance(key, str):
            parts = [part.strip() for part in key.split(sep)] if key.strip() else []
            if any(not part for part in parts):
                raise ValueError(f"malformed intersection key: {key!r}")
            names = tuple(parts)
        elif isinstance(key, (tuple, list)):
            names = tuple(key)
        elif isinstance(key, (set, frozenset)):
            raise TypeError(
                f"intersection keys must be ordered (str, tuple, or list), got a "
                f"{type(key).__name__}: {key!r}; use a tuple so the set display "
                "order is deterministic"
            )
        else:
            raise TypeError(f"invalid intersection key: {key!r}")
        names = tuple(_validated_membership(names, f"counts key {key!r}"))
        if isinstance(size, bool) or not isinstance(size, (int, float)):
            raise TypeError(f"size for {key!r} must be a number, got {size!r}")
        if not math.isfinite(size) or size < 0:
            raise ValueError(f"size for {key!r} must be a finite number >= 0, got {size!r}")
        combo = frozenset(names)
        if combo in seen:
            raise ValueError(
                f"intersection {key!r} duplicates {seen[combo]!r}: the same set "
                "combination appears more than once"
            )
        seen[combo] = key
        for name in names:
            set_order.setdefault(name)
        parsed.append((names, size))
    index = {name: position for position, name in enumerate(set_order)}
    intersections = tuple(
        UpSetIntersection(
            sets=tuple(sorted(names, key=index.__getitem__)),
            size=size,
        )
        for names, size in parsed
    )
    set_sizes = tuple(
        sum(entry.size for entry in intersections if name in entry.sets) for name in set_order
    )
    return UpSetData(
        set_names=tuple(set_order),
        set_sizes=set_sizes,
        intersections=intersections,
    )


def _direction(sort_by: str, valid: tuple[str, ...], what: str) -> tuple[str, bool]:
    reverse = sort_by.startswith("-")
    key = sort_by[1:] if reverse else sort_by
    if key not in valid:
        options = ", ".join(repr(option) for option in valid)
        raise ValueError(
            f"{what} must be one of {options} (optionally prefixed with '-' to "
            f"reverse), got {sort_by!r}"
        )
    return key, reverse


def sort_intersections(
    intersections: Sequence[UpSetIntersection],
    set_names: Sequence[str],
    sort_by: str = "cardinality",
) -> tuple[UpSetIntersection, ...]:
    """Order intersections for display.

    ``sort_by`` is one of ``"cardinality"`` (largest first), ``"degree"``
    (fewest participating sets first, ties by size), or ``"input"`` (the
    order they were built in). Prefix with ``-`` to reverse. Ties are broken
    deterministically by the participating sets' display order.
    """
    key, reverse = _direction(sort_by, ("cardinality", "degree", "input"), "sort_by")
    index = {name: position for position, name in enumerate(set_names)}

    def combo_key(intersection: UpSetIntersection) -> tuple[int, ...]:
        return tuple(sorted(index[name] for name in intersection.sets))

    if key == "cardinality":
        ordered = sorted(
            intersections,
            key=lambda entry: (-entry.size, entry.degree, combo_key(entry)),
        )
    elif key == "degree":
        ordered = sorted(
            intersections,
            key=lambda entry: (entry.degree, -entry.size, combo_key(entry)),
        )
    else:
        ordered = list(intersections)
    if reverse:
        ordered.reverse()
    return tuple(ordered)


def sort_sets(
    set_names: Sequence[str],
    set_sizes: Sequence[float],
    sort_by: str = "cardinality",
) -> tuple[str, ...]:
    """Order set names for display.

    ``sort_by`` is one of ``"cardinality"`` (largest first), ``"name"``
    (alphabetical), or ``"input"``. Prefix with ``-`` to reverse. Ties keep
    the input order.
    """
    key, reverse = _direction(sort_by, ("cardinality", "name", "input"), "sort_sets_by")
    pairs = list(zip(set_names, set_sizes))
    if key == "cardinality":
        pairs.sort(key=lambda pair: -pair[1])
    elif key == "name":
        pairs.sort(key=lambda pair: pair[0])
    ordered = [name for name, _size in pairs]
    if reverse:
        ordered.reverse()
    return tuple(ordered)
