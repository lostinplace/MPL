import dataclasses
import itertools
from typing import FrozenSet

from mpl.Parser.ExpressionParsers import Reference


@dataclasses.dataclass(frozen=True)
class EntityValue:
    value: FrozenSet = frozenset()

    @staticmethod
    def from_value(value):
        match value:
            case x if not x:
                return EntityValue()
            case set() | frozenset() | list() | tuple():
                tmp = frozenset(value)
                return EntityValue(tmp)
            case EntityValue():
                return value
            case x:
                tmp = frozenset({x})
                return EntityValue(tmp)

    @property
    def references(self) -> FrozenSet[Reference]:
        return frozenset({x for x in self.value if isinstance(x, Reference)})

    @property
    def clean(self):
        only_truth = frozenset(x for x in self.value if x)
        return EntityValue(only_truth)

    def __or__(self, other):
        match other:
            case EntityValue():
                return EntityValue(self.value | other.value)
            case set() | frozenset():
                return EntityValue(self.value | other)
            case x:
                return EntityValue(self.value | {x})

    def __ror__(self, other):
        return self | other

    def __str__(self):
        values = sorted(self.value, key=str)
        value_str = ', '.join(str(v) for v in values)
        return f'{{{value_str}}}'

    def without(self, other: 'EntityValue'):
        return EntityValue(self.value - other.value)

    def __bool__(self):
        return any([x for x in self.value if x and not isinstance(x, Reference)])

    def __add__(self, other):
        other = EntityValue.from_value(other)
        combinations = itertools.product(self.value, other.value)
        return EntityValue.from_value(x+y for x, y in combinations)

    def __sub__(self, other):
        other = EntityValue.from_value(other)
        combinations = itertools.product(self.value, other.value)
        return EntityValue.from_value(x-y for x, y in combinations)

    def __mul__(self, other):
        other = EntityValue.from_value(other)
        combinations = itertools.product(self.value, other.value)
        return EntityValue.from_value(x*y for x, y in combinations)

    def __truediv__(self, other):
        other = EntityValue.from_value(other)
        combinations = itertools.product(self.value, other.value)
        return EntityValue.from_value(x/y for x, y in combinations)

    def __floordiv__(self, other):
        other = EntityValue.from_value(other)
        combinations = itertools.product(self.value, other.value)
        return EntityValue.from_value(x//y for x, y in combinations)

    def __pow__(self, power, modulo=None):
        if modulo is not None:
            raise NotImplementedError('Modulo is not supported')
        power = EntityValue.from_value(power)
        combinations = itertools.product(self.value, power.value)
        return EntityValue.from_value(x**y for x, y in combinations)

    def __eq__(self, other):
        if not isinstance(other, EntityValue):
            return EntityValue()
        if self.value == other.value:
            return self
        return false_value

    def __ne__(self, other):
        if not isinstance(other, EntityValue):
            return self or true_value
        if self.value == other.value:
            return false_value
        return self or other or true_value

    def __lt__(self, other):
        if len(self.value) < len(other.value):
            return other or true_value
        elif len(self.value) > len(other.value):
            return false_value

        result = set()
        for x, y in itertools.product(self.value, other.value):
            result.add(x < y)

        if all(result):
            return self or true_value
        return false_value

    def __le__(self, other):
        if len(self.value) < len(other.value):
            return other or true_value
        elif len(self.value) > len(other.value):
            return false_value

        result = set()
        for x, y in itertools.product(self.value, other.value):
            result.add(x <= y)

        if all(result):
            return self or true_value
        return false_value

    def __gt__(self, other):
        if len(self.value) > len(other.value):
            return other or true_value
        elif len(self.value) < len(other.value):
            return false_value

        result = set()
        for x, y in itertools.product(self.value, other.value):
            result.add(x > y)

        if all(result):
            return self or true_value
        return false_value

    def __ge__(self, other):
        if len(self.value) > len(other.value):
            return other or true_value
        elif len(self.value) < len(other.value):
            return false_value

        result = set()
        for x, y in itertools.product(self.value, other.value):
            result.add(x >= y)

        if all(result):
            return self or true_value
        return false_value


true_value = EntityValue.from_value(1)
false_value = EntityValue()

