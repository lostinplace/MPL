from dataclasses import dataclass
from typing import Any, Tuple

from mpl.lib.quick_filter_set import filter_set


@dataclass(frozen=True, order=True)
class TestDataClass:
    name: str
    bait: Any


def test_ok():
    test_set = {
        'a',
        1,
        ('b', 2),
        ('a', 2, 'c'),
        ('a', 2, 3),
        TestDataClass('bodyguard', 'long lost pal'),
        TestDataClass('eddie', 'al'),
        TestDataClass('man walks down the street', 'hoom'),
    }

    result = filter_set(test_set, TestDataClass(Any, 'al'))
    assert result == {
        TestDataClass('eddie', 'al'),
    }

    result = filter_set(test_set, ('b', Any))
    assert result == {
        ('b', 2),
    }

    result = filter_set(test_set, Tuple)
    assert result == {
        ('b', 2),
        ('a', 2, 'c'),
        ('a', 2, 3)
    }

    result = filter_set(test_set, 'a')
    assert result == {'a',}

    result = filter_set(test_set, 1)
    assert result == {1, }

    result = filter_set(test_set, {1, 'a'})
    assert result == {1, 'a'}

    result = filter_set(test_set, test_set)
    assert result == test_set