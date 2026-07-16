import pytest

from dash_upset import UpSetData, from_memberships

# Six elements across three sets, including one element in no set. Expected
# exclusive intersections, in first-appearance order:
#   (A,): 1 [a]   (A, B): 2 [b, c]   (B,): 1 [d]   (): 1 [e]   (A, B, C): 1 [f]
# Set totals: A=4, B=4, C=1. Total elements: 6.
SAMPLE_MEMBERSHIPS = [
    ("A",),
    ("A", "B"),
    ("A", "B"),
    ("B",),
    (),
    ("A", "B", "C"),
]
SAMPLE_IDS = ["a", "b", "c", "d", "e", "f"]


@pytest.fixture
def sample() -> UpSetData:
    return from_memberships(SAMPLE_MEMBERSHIPS, element_ids=SAMPLE_IDS)
