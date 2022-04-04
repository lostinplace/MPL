import dataclasses
import itertools
from typing import FrozenSet

from sympy import Symbol, Expr
from sympy.core.relational import Relational

from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference


@dataclasses.dataclass(frozen=True)
class EntityValue:
    value: FrozenSet = frozenset()
    p: float = 1.0

    @staticmethod
    def from_value(*args):
        if args and isinstance(args[0], Expr):
            pass
        match args:
            case(Relational() as x, ):
                return EntityValue(frozenset({x}))
            case (x,) if not x:
                return EntityValue()
            case (EntityValue() as x, ):
                return x
            case [] as x if not x:
                return EntityValue()
            case [*x] if len(x) > 1:
                tmp = frozenset(args)
                return EntityValue(tmp)
            case (set() | list() | tuple() | frozenset(),):
                tmp = frozenset(args[0])
                return EntityValue(tmp)
            case [EntityValue()]:
                return args[0]
            case [_]:
                tmp = frozenset(args)
                return EntityValue(tmp)
            case _:
                return None

    @property
    def references(self) -> FrozenSet[Reference]:
        return frozenset({x for x in self.value if isinstance(x, Reference)})

    @property
    def clean(self):
        only_truth = frozenset(x for x in self.value if x)
        return EntityValue(only_truth)

    @property
    def free_symbols(self) -> FrozenSet[Symbol]:
        result = set()
        for item in self:
            if isinstance(item, Expr):
                result |= item.free_symbols
        return frozenset(result)

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
        tmp = len([x for x in self.value if not isinstance(x, Reference)])
        return bool(tmp)

    def __add__(self, other):
        other = EntityValue.from_value(other)
        combinations = itertools.product(self.value, other.value)
        return EntityValue.from_value({x+y for x, y in combinations})

    def __sub__(self, other):
        other = EntityValue.from_value(other)
        combinations = itertools.product(self.value, other.value)
        return EntityValue.from_value({x-y for x, y in combinations})

    def __mul__(self, other):
        other = EntityValue.from_value(other)
        combinations = itertools.product(self.value, other.value)
        return EntityValue.from_value({x*y for x, y in combinations})

    def __truediv__(self, other):
        other = EntityValue.from_value(other)
        combinations = itertools.product(self.value, other.value)
        return EntityValue.from_value({x/y for x, y in combinations})

    def __floordiv__(self, other):
        other = EntityValue.from_value(other)
        combinations = itertools.product(self.value, other.value)
        return EntityValue.from_value({x//y for x, y in combinations})

    def __pow__(self, power, modulo=None):
        if modulo is not None:
            raise NotImplementedError('Modulo is not supported')
        power = EntityValue.from_value(power)
        combinations = itertools.product(self.value, power.value)
        return EntityValue.from_value({x**y for x, y in combinations})

    def __eq__(self, other):
        if not isinstance(other, EntityValue):
            return false_value
        if self.value == other.value:
            return self or true_value
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

    def __gt__(self, other: 'EntityValue'):
        if not other:
            return self or true_value
        if other and not self:
            return false_value

        comparisons = set(itertools.product(self.value, other.value))
        gt_results = set()
        inequalities = set()
        for x, y in comparisons:
            comp = x > y
            match comp:
                case False:
                    continue
                case True:
                    gt_results.add(x)
                case Relational():
                    inequalities.add(comp)

        if inequalities:
            return false_value

        if len(gt_results) / len(comparisons) > 0.5:
            return ev_fv(gt_results)
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

    def __iter__(self):
        return iter(self.value)

    @property
    def expressions(self) -> FrozenSet[Expr]:
        return frozenset(x for x in self.value if isinstance(x, Expr))

    def with_p(self, p: float) -> 'EntityValue':
        return dataclasses.replace(self, p=p)



ev_fv = EntityValue.from_value

true_value = EntityValue.from_value(1)
false_value = EntityValue()
