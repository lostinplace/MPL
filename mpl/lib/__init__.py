from typing import Any


def fs(*items: Any) -> frozenset:
    return frozenset(tuple(items))


def hash_dict(d: dict) -> int:
    return hash(frozenset(d.items()))