"""Tests for the UpSetData model and its constructors."""

import pandas as pd
import polars as pl
import pytest

from dash_upset import (
    UpSetData,
    UpSetIntersection,
    from_contents,
    from_counts,
    from_indicators,
    from_memberships,
)
from dash_upset.data import sort_intersections, sort_sets, subset_sizes
from tests.conftest import SAMPLE_IDS, SAMPLE_MEMBERSHIPS


def by_combo(data: UpSetData) -> dict:
    return {frozenset(entry.sets): entry for entry in data.intersections}


class TestFromMemberships:
    def test_sets_discovered_in_first_appearance_order(self, sample):
        assert sample.set_names == ("A", "B", "C")
        assert sample.set_sizes == (4, 4, 1)

    def test_exclusive_intersections(self, sample):
        combos = by_combo(sample)
        assert combos[frozenset({"A"})].size == 1
        assert combos[frozenset({"A", "B"})].size == 2
        assert combos[frozenset({"B"})].size == 1
        assert combos[frozenset()].size == 1
        assert combos[frozenset({"A", "B", "C"})].size == 1
        assert len(sample.intersections) == 5
        assert sample.total_size == 6

    def test_elements_and_degree(self, sample):
        combos = by_combo(sample)
        assert combos[frozenset({"A", "B"})].elements == ("b", "c")
        assert combos[frozenset({"A", "B"})].degree == 2
        assert combos[frozenset()].elements == ("e",)
        assert combos[frozenset()].degree == 0

    def test_member_sets_ordered_by_set_order(self, sample):
        combos = by_combo(sample)
        assert combos[frozenset({"A", "B", "C"})].sets == ("A", "B", "C")

    def test_default_element_ids_are_positions(self):
        data = from_memberships(SAMPLE_MEMBERSHIPS)
        assert by_combo(data)[frozenset({"A", "B"})].elements == (1, 2)

    def test_element_ids_length_mismatch(self):
        with pytest.raises(ValueError, match="element_ids"):
            from_memberships([("A",)], element_ids=["x", "y"])

    def test_bare_string_membership_rejected(self):
        with pytest.raises(TypeError, match="string"):
            from_memberships(["AB"])

    def test_duplicate_set_within_membership_rejected(self):
        with pytest.raises(ValueError, match="more than once"):
            from_memberships([("A", "A")])

    def test_empty_input(self):
        data = from_memberships([])
        assert data == UpSetData((), (), ())


class TestFromContents:
    def test_matches_memberships(self, sample):
        data = from_contents({"A": ["a", "b", "c", "f"], "B": ["b", "c", "d", "f"], "C": ["f"]})
        assert data.set_names == sample.set_names
        assert data.set_sizes == sample.set_sizes
        expected = {
            combo: entry.size
            for combo, entry in by_combo(sample).items()
            if combo  # contents cannot express elements in no set
        }
        assert {c: e.size for c, e in by_combo(data).items()} == expected

    def test_duplicate_elements_counted_once(self):
        data = from_contents({"A": ["x", "x", "y"]})
        assert data.set_sizes == (2,)

    def test_string_contents_rejected(self):
        with pytest.raises(TypeError, match="string"):
            from_contents({"A": "xyz"})


# The indicator equivalent of SAMPLE_MEMBERSHIPS (rows align with SAMPLE_IDS).
SAMPLE_INDICATORS = {
    "A": [True, True, True, False, False, True],
    "B": [False, True, True, True, False, True],
    "C": [False, False, False, False, False, True],
}


class TestFromIndicators:
    def test_pandas_dataframe_index_provides_ids(self, sample):
        frame = pd.DataFrame(SAMPLE_INDICATORS, index=SAMPLE_IDS)
        assert from_indicators(frame) == sample

    def test_polars_dataframe_ids_are_positional(self):
        frame = pl.DataFrame(SAMPLE_INDICATORS)
        assert from_indicators(frame) == from_memberships(SAMPLE_MEMBERSHIPS)

    def test_element_ids_parameter(self, sample):
        frame = pl.DataFrame(SAMPLE_INDICATORS)
        assert from_indicators(frame, element_ids=SAMPLE_IDS) == sample

    def test_element_ids_override_pandas_index(self):
        frame = pd.DataFrame({"A": [True, False]}, index=["x", "y"])
        data = from_indicators(frame, element_ids=["u", "v"])
        assert by_combo(data)[frozenset({"A"})].elements == ("u",)

    def test_element_ids_length_mismatch(self):
        with pytest.raises(ValueError, match="element_ids"):
            from_indicators({"A": [True, False]}, element_ids=["x"])

    def test_mapping_input(self):
        data = from_indicators({"A": [True, False], "B": [True, True]})
        assert data.set_names == ("A", "B")
        assert data.set_sizes == (1, 2)

    def test_mapping_ragged_columns_rejected(self):
        with pytest.raises(ValueError, match="equal lengths"):
            from_indicators({"A": [True], "B": [True, False]})

    def test_mapping_non_boolean_value_rejected(self):
        with pytest.raises(ValueError, match="boolean"):
            from_indicators({"A": [True, 2]})

    def test_zero_one_integers_accepted(self):
        assert from_indicators(pd.DataFrame({"A": [1, 0, 1]})).set_sizes == (2,)
        assert from_indicators(pl.DataFrame({"A": [1, 0, 1]})).set_sizes == (2,)

    def test_out_of_range_integers_rejected(self):
        with pytest.raises(ValueError, match="other than 0 and 1"):
            from_indicators(pl.DataFrame({"A": [0, 2]}))

    def test_non_boolean_column_rejected(self):
        with pytest.raises(ValueError, match="boolean"):
            from_indicators(pd.DataFrame({"A": [0.5, 1.0]}))

    def test_missing_values_rejected(self):
        frame = pd.DataFrame({"A": pd.array([True, pd.NA], dtype="boolean")})
        with pytest.raises(ValueError, match="missing"):
            from_indicators(frame)
        with pytest.raises(ValueError, match="missing"):
            from_indicators(pl.DataFrame({"A": [True, None]}))

    def test_non_string_column_rejected(self):
        with pytest.raises(ValueError, match="set names"):
            from_indicators(pd.DataFrame({0: [True]}))

    def test_lazyframe_rejected(self):
        with pytest.raises(TypeError, match="eager"):
            from_indicators(pl.LazyFrame({"A": [True]}))

    def test_wrong_type_rejected(self):
        with pytest.raises(TypeError, match="narwhals-supported"):
            from_indicators([[True, False]])


class TestFromCounts:
    def test_string_and_tuple_keys(self):
        data = from_counts({"A": 1, "A & B": 2, ("B",): 1, ("A", "B", "C"): 1})
        assert data.set_names == ("A", "B", "C")
        assert data.set_sizes == (4, 4, 1)
        assert by_combo(data)[frozenset({"A", "B"})].size == 2
        assert all(entry.elements is None for entry in data.intersections)

    def test_empty_key_means_no_sets(self):
        data = from_counts({"": 2, "A": 1})
        assert data.set_names == ("A",)
        assert by_combo(data)[frozenset()].size == 2
        assert data.total_size == 3

    def test_float_sizes_accepted(self):
        data = from_counts({"A": 1.5})
        assert data.set_sizes == (1.5,)

    def test_colliding_combinations_rejected(self):
        with pytest.raises(ValueError, match="appears more than once"):
            from_counts({"A&B": 1, ("B", "A"): 2})

    def test_unordered_key_rejected(self):
        with pytest.raises(TypeError, match="ordered"):
            from_counts({frozenset({"A"}): 1})

    def test_malformed_string_key_rejected(self):
        with pytest.raises(ValueError, match="malformed"):
            from_counts({"A&&B": 1})

    def test_negative_size_rejected(self):
        with pytest.raises(ValueError, match="finite number"):
            from_counts({"A": -1})

    def test_non_numeric_size_rejected(self):
        with pytest.raises(TypeError, match="number"):
            from_counts({"A": "12"})

    def test_custom_separator(self):
        data = from_counts({"A|B": 3}, sep="|")
        assert by_combo(data)[frozenset({"A", "B"})].size == 3


class TestModelValidation:
    def test_negative_intersection_size(self):
        with pytest.raises(ValueError, match=">= 0"):
            UpSetIntersection(sets=("A",), size=-1)

    def test_elements_size_mismatch(self):
        with pytest.raises(ValueError, match="elements"):
            UpSetIntersection(sets=("A",), size=2, elements=("x",))

    def test_duplicate_sets_in_intersection(self):
        with pytest.raises(ValueError, match="duplicate"):
            UpSetIntersection(sets=("A", "A"), size=1)

    def test_names_sizes_length_mismatch(self):
        with pytest.raises(ValueError, match="set sizes"):
            UpSetData(("A",), (1, 2), ())

    def test_unknown_set_in_intersection(self):
        with pytest.raises(ValueError, match="unknown"):
            UpSetData(("A",), (1,), (UpSetIntersection(("B",), 1),))

    def test_set_size_lookup(self, sample):
        assert sample.set_size("C") == 1
        with pytest.raises(KeyError):
            sample.set_size("missing")


class TestSorting:
    def test_cardinality_default(self, sample):
        ordered = sort_intersections(sample.intersections, sample.set_names)
        assert [entry.sets for entry in ordered] == [
            ("A", "B"),  # size 2
            (),  # size 1, degree 0
            ("A",),  # size 1, degree 1, first set
            ("B",),  # size 1, degree 1, second set
            ("A", "B", "C"),  # size 1, degree 3
        ]

    def test_cardinality_reversed(self, sample):
        ordered = sort_intersections(sample.intersections, sample.set_names, "-cardinality")
        assert ordered[-1].sets == ("A", "B")

    def test_degree(self, sample):
        ordered = sort_intersections(sample.intersections, sample.set_names, "degree")
        assert [entry.degree for entry in ordered] == [0, 1, 1, 2, 3]

    def test_input_preserved(self, sample):
        ordered = sort_intersections(sample.intersections, sample.set_names, "input")
        assert ordered == sample.intersections

    def test_invalid_sort_by(self, sample):
        with pytest.raises(ValueError, match="sort_by"):
            sort_intersections(sample.intersections, sample.set_names, "size")

    def test_sort_sets(self):
        names, sizes = ("b", "a", "c"), (2, 5, 2)
        assert sort_sets(names, sizes) == ("a", "b", "c")
        assert sort_sets(names, sizes, "-cardinality") == ("c", "b", "a")
        assert sort_sets(names, sizes, "name") == ("a", "b", "c")
        assert sort_sets(names, sizes, "-name") == ("c", "b", "a")
        assert sort_sets(names, sizes, "input") == ("b", "a", "c")
        with pytest.raises(ValueError, match="sort_sets_by"):
            sort_sets(names, sizes, "size")


class TestSubsetModes:
    def sizes(self, data, mode):
        return {frozenset(entry.sets): entry.size for entry in subset_sizes(data, mode)}

    def test_distinct_is_identity(self, sample):
        assert subset_sizes(sample, "distinct") == sample.intersections

    def test_intersect_sizes(self, sample):
        sizes = self.sizes(sample, "intersect")
        assert sizes[frozenset({"A"})] == 4  # every element of A
        assert sizes[frozenset({"A", "B"})] == 3  # in both A and B (incl. A&B&C)
        assert sizes[frozenset({"B"})] == 4
        assert sizes[frozenset({"A", "B", "C"})] == 1
        assert sizes[frozenset()] == 1  # the "no set" subset passes through

    def test_union_sizes(self, sample):
        sizes = self.sizes(sample, "union")
        assert sizes[frozenset({"A", "B"})] == 5  # in A or B
        assert sizes[frozenset({"A", "B", "C"})] == 5
        assert sizes[frozenset({"A"})] == 4

    def test_singletons_equal_set_size(self, sample):
        for mode in ("intersect", "union"):
            sizes = self.sizes(sample, mode)
            assert sizes[frozenset({"A"})] == sample.set_size("A")
            assert sizes[frozenset({"B"})] == sample.set_size("B")

    def test_intersect_le_union(self, sample):
        inter = self.sizes(sample, "intersect")
        union = self.sizes(sample, "union")
        assert all(inter[combo] <= union[combo] for combo in inter)

    def test_elements_recomputed(self, sample):
        by = {frozenset(e.sets): e for e in subset_sizes(sample, "intersect")}
        assert set(by[frozenset({"A", "B"})].elements) == {"b", "c", "f"}

    def test_counts_input_has_no_elements(self):
        data = from_counts({"A": 1, "A&B": 2, "B": 1, "A&B&C": 1})
        assert all(entry.elements is None for entry in subset_sizes(data, "union"))

    def test_invalid_mode(self, sample):
        with pytest.raises(ValueError, match="mode must be one of"):
            subset_sizes(sample, "exclusive")


def test_constructors_agree(sample):
    contents = from_contents({"A": ["a", "b", "c", "f"], "B": ["b", "c", "d", "f"], "C": ["f"]})
    counts = from_counts({"A": 1, "A&B": 2, "B": 1, "": 1, "A&B&C": 1})
    assert contents.set_names == counts.set_names == sample.set_names
    assert contents.set_sizes == counts.set_sizes == sample.set_sizes
    sample_sizes = {combo: entry.size for combo, entry in by_combo(sample).items()}
    counts_sizes = {combo: entry.size for combo, entry in by_combo(counts).items()}
    assert counts_sizes == sample_sizes
