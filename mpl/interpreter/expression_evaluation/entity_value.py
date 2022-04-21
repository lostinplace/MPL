import dataclasses
import itertools
from typing import FrozenSet

from sympy import Symbol, Expr
from sympy.core.relational import Relational, Eq
from sympy.logic.boolalg import BooleanTrue, BooleanFalse

from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference, Ref
from mpl.lib.relational_math import simplify_relational_set


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
        truthy_vals = {x for x in self.value if x}
        if len([x for x in truthy_vals if not isinstance(x, Ref)]) > 1:
            tmp = frozenset(x for x in truthy_vals if not x is True)
            return EntityValue(tmp)
        return EntityValue(frozenset(truthy_vals), self.p)

    @property
    def organize_relationals(self):
        relations = {x for x in self.value if isinstance(x, Relational)}
        remaining = self.value - relations
        simplified = simplify_relational_set(relations)
        new_values = remaining | simplified
        return EntityValue(new_values, self.p)

    @property
    def free_symbols(self) -> FrozenSet[Symbol]:
        result = set()
        for item in self:
            if isinstance(item, Expr):
                result |= item.free_symbols
        return frozenset(result)

    @property
    def expressions(self) -> FrozenSet[Expr]:
        return frozenset(x for x in self.value if isinstance(x, (Expr, Relational)))

    def __iter__(self):
        return iter(self.value)

    def with_p(self, p: float) -> 'EntityValue':
        return dataclasses.replace(self, p=p)

    def without(self, other: 'EntityValue'):
        return EntityValue(self.value - other.value)

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

    def __bool__(self):
        tmp = len([x for x in self.value if not isinstance(x, Reference)])
        return bool(tmp)

    # region algebra

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

    # endregion

    # region comparison

    def __eq__(self, other):
        return process_entity_value_equality(self, other)

    def __ne__(self, other):
        tmp = self == other
        if tmp:
            return false_value
        return self or true_value

    def __lt__(self, other):
        return process_entity_value_comparison(self, other, lambda x, y: x < y)

    def __le__(self, other):
        return process_entity_value_comparison(self, other, lambda x, y: x <= y)

    def __gt__(self, other: 'EntityValue'):
        return process_entity_value_comparison(self, other, lambda x, y: x > y)

    def __ge__(self, other):
        return process_entity_value_comparison(self, other, lambda x, y: x >= y)

    # endregion


def process_entity_value_equality(x: EntityValue, y: EntityValue) -> EntityValue:
    if not x and not y:
        return true_value
    if not x or not y:
        return false_value

    inequality = set()

    intersection = x.value & y.value
    left_over = (x.value | y.value) - intersection

    all_relationals = {a for a in left_over if isinstance(a, Relational)}

    all_refs = {a for a in left_over if isinstance(a, Ref)}

    x_comparable = x.value - intersection - all_refs - all_relationals
    y_comparable = y.value - intersection - all_refs - all_relationals

    if len(x_comparable) != len(y_comparable):
        return false_value

    all_eqs = set(itertools.product(x_comparable, y_comparable))

    eq_results = set()

    # region strict equality pass

    tmp = {(x, y) for x, y in all_eqs if x == y is True or (x == y) == BooleanTrue()}
    tmp = set(itertools.chain(*tmp))
    eq_results |= tmp

    # endregion

    # region symbolic equality pass

    all_equalities = {(x, y, Eq(x, y)) for x, y in all_eqs if x not in eq_results and y not in eq_results}
    for value_a, value_b, eq in all_equalities:
        match eq:
            case Eq():
                eq_results.add(eq)
            case BooleanTrue():
                eq_results |= {value_a, value_b}
            case BooleanFalse():
                return false_value

    # endregion

    all_relationals_reduced = simplify_relational_set(frozenset(all_relationals))
    if all_relationals_reduced is False:
        return false_value

    final_result_set = intersection | all_relationals_reduced | eq_results | all_refs
    return EntityValue.from_value(final_result_set)


def process_entity_value_comparison(x: EntityValue, y: EntityValue, comparison, threshold=0.5) -> EntityValue:
    # a comparison produces a value comprised of all of the components of the two values that meet the
    # condition provided.  The resulting entityvalue has a p that reflects the number of pootential  comparisons
    # that met the condition (right now the default is 0.5, if the p is below that, false_value is returrned)
    # when two values are compared, in order to be truthy, all of the relationals created by th ecomparrisons must be
    # true, ootherwise we would advance a known false hypothesis.
    #  when a conditiono results in a relational it is added to the result.
    #  references are ignored

    if not y and comparison(1, 0):
        return x or true_value
    elif not y:
        return false_value
    elif y and not x and comparison(0, 1):
        return true_value
    if y and not x:
        return false_value

    x_relational = {a for a in x if isinstance(a, Relational)}
    y_relational = {a for a in y if isinstance(a, Relational)}
    all_relationals = x_relational | y_relational

    x_refs = {a for a in x if isinstance(a, Ref)}
    y_refs = {a for a in y if isinstance(a, Ref)}

    x_comparable = x.value - x_relational - x_refs
    y_comparable = y.value - y_relational - y_refs
    y_comparable = y_comparable or {0}

    comparison_product = {(x, y, comparison(x, y)) for x, y in itertools.product(x_comparable, y_comparable)}

    total_true = 0
    total_count = 0
    out_set = set()
    for value, _, result in comparison_product:
        total_count += 1
        match result:
            case Relational():
                all_relationals.add(result)
            case x if not x:
                continue
        out_set.add(value)
        total_true += 1

    all_relationals_reduced = simplify_relational_set(frozenset(all_relationals))
    if all_relationals_reduced is False:
        return false_value

    p = (total_true / total_count) if total_count else 1
    if p < threshold:
        return false_value

    new_values = x_comparable | all_relationals_reduced | x_refs

    return EntityValue(new_values, p)


ev_fv = EntityValue.from_value

true_value = EntityValue.from_value(True)
false_value = EntityValue()
