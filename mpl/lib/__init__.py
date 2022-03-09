from typing import Any


def fs(*items: Any) -> frozenset:
    return frozenset(tuple(items))
