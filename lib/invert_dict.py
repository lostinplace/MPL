from collections import defaultdict
from typing import TypeVar, Dict, Set

KT = TypeVar('KT')
VT = TypeVar('VT')


def invert_dict(source: Dict[KT, VT]) -> Dict[VT, Set[KT]]:
    out_dict: Dict[VT, Set[KT]] = defaultdict(set)
    for k, v in source.items():
        out_dict[v].add(k)

    return out_dict


def test_invert_dict():
    source_dict = {
        'a': 1,
        'b': 2,
        'c': 1,
        'd': 3
    }

    expected = {
        1: {'a', 'c'},
        2: {'b'},
        3: {'d'},
    }

    actual = invert_dict(source_dict)
    assert actual == expected