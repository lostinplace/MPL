import dataclasses
from enum import Flag, auto
from typing import Any, Set, TypeVar, Tuple, Union, Callable, Type

T = TypeVar('T')

typ = Union[int, str]


class QuickFilterComparisons(Flag):
    EQUALITY = auto()
    SET_MEMBERSHIP = auto()
    STRICT_TYPE_CHECK = auto()
    CALLABLE_CRITERIA = auto()
    DATACLASS_FILTER = auto()
    VARIABLE_TYPE_CHECK = auto()
    TUPLE_COMPARISON = auto()
    ALL = EQUALITY | SET_MEMBERSHIP | STRICT_TYPE_CHECK | \
          CALLABLE_CRITERIA | DATACLASS_FILTER | VARIABLE_TYPE_CHECK | \
          TUPLE_COMPARISON


def filter_set(source_set: Set[T], criteria: Any, comparisons: QuickFilterComparisons = QuickFilterComparisons.ALL) -> Set[T]:
    """
    Quickly filters a set based on some nutty criteria
    :param source_set: the set to be filtered
    :param criteria: the criteria to applied
    :param comparisons: the comparisons to be performed
    :return: a new set with only the allowed elements
    """

    out = set()

    for item in source_set:
        result = quick_filter_compare(item, criteria, comparisons)
        if result:
            out.add(item)

    return out


def quick_filter_compare(item, criteria, comparisons: QuickFilterComparisons = QuickFilterComparisons.ALL) -> bool:
    qfc = QuickFilterComparisons

    if comparisons & qfc.EQUALITY and item == criteria:
        return True

    if comparisons & qfc.SET_MEMBERSHIP and isinstance(criteria, set) and item in criteria :
        return True

    if comparisons & qfc.STRICT_TYPE_CHECK and isinstance(criteria, Type) and isinstance(item, criteria):
        return True

    if comparisons & qfc.DATACLASS_FILTER \
            and dataclasses.is_dataclass(item) \
            and dataclasses.is_dataclass(criteria) \
            and type(item) == type(criteria):

        item_values = item.__annotations__
        for k in item_values:
            result = quick_filter_compare(getattr(item, k), getattr(criteria, k), comparisons)
            if not result:
                return False
        return True

    if comparisons & qfc.VARIABLE_TYPE_CHECK \
            and hasattr(criteria, '__module__') \
            and criteria.__module__ in {'typing', 'builtins'}:

        # TODO: Optional Should be used to include None
        if criteria is Any or isinstance(item, criteria):
            return True

    if comparisons & qfc.CALLABLE_CRITERIA and isinstance(criteria, Callable):
        try:
            result = criteria(item)
            if result is True:
                return True
        except:
            pass
        finally:
            pass

    if comparisons & qfc.TUPLE_COMPARISON \
            and isinstance(item, Tuple) \
            and isinstance(criteria, Tuple) \
            and len(item) == len(criteria):
        for i, v in enumerate(item):
            result = quick_filter_compare(v, criteria[i], comparisons)
            if not result:
                return False
        return True

    return False

