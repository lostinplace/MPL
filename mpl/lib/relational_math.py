from symtable import Symbol
from typing import FrozenSet, Optional

from sympy import symbols, And
from sympy.core.numbers import oo
from sympy.core.relational import Relational, Eq, _Inequality
from sympy.logic.boolalg import BooleanFalse

from mpl.lib import fs


red, black, uncolored = symbols('red black uncolored')

infinities = {oo, -oo}


def clean_relational(rel: Relational, symbol: Symbol) -> Optional[Relational]:
    match rel:
        case Eq() if symbol in rel.free_symbols and rel.lhs != symbol:
            return rel.reversed
        case _Inequality() if set(rel.args) & infinities:
            return None
        case _Inequality() if symbol in rel.free_symbols and rel.lhs != symbol:
            return rel.reversed
    return rel


def boolean_to_rel_set(boolean: And, symbol: Symbol) -> FrozenSet[Relational]:
    result = set()
    for x in boolean.args:
        if isinstance(x, Relational):
            tmp = clean_relational(x, symbol)
            if tmp is not None:
                result.add(tmp)
    return frozenset(result)


def ineq_resolver(inequalities: FrozenSet[Relational], symbol: Symbol) -> FrozenSet[Relational] | bool:
    from sympy import reduce_inequalities

    tmp = reduce_inequalities(inequalities, [symbol])
    match tmp:
        case BooleanFalse():
            return False
        case And() as x:
            return boolean_to_rel_set(x, symbol)
        case Relational():
            return frozenset([tmp])


def get_free_symbols_from_relational_set(rel: FrozenSet[Relational]) -> FrozenSet[Symbol]:
    result = set()
    for x in rel:
        result |= x.free_symbols
    return frozenset(result)


def simplify_relational_set(inequalities: FrozenSet[Relational]) -> FrozenSet[Relational] | bool:
    if not inequalities:
        return frozenset()
    free_symbols = get_free_symbols_from_relational_set(inequalities)
    first_symbol = sorted(free_symbols, key=str)[0]
    return ineq_resolver(inequalities, first_symbol)


def test_reduction_of_multiple_univariate_inequalities():
    expectations = {
        fs(red < 13, red < 9, red < 7, red > 3, red > -2): fs(red < 7, red > 3),
        fs(red < 5, red > 2): fs(red < 5, red > 2),
        fs(red > 3, red < 1): fs(),
        fs(red > 3, red > 1): fs(3 < red),
        fs(red > 3, red > 1, red < -2): fs(),
    }

    for ineq, expected in expectations.items():
        actual = ineq_resolver(ineq, red)
        assert actual == expected


def test_complicated_reduction_of_multiple_enqualities():
    expectations = {
        fs(-3 * red < 3 * red + 18, red > -12, 2 * red < -3 * red): frozenset({red < 0, red > -3}),
    }

    for ineq, expected in expectations.items():
        actual = simplify_relational_set(ineq)
        assert actual == expected


def test_simple_reduction_of_bivariate_inequalities():
    red_val = 3
    black_val = 7

    expectations = {
        fs(
            5 * red > 2 * black,
            red < black,
            red < black + 2,
            1.5 * red < black - 1,
        ): fs(red < black - 1),
    }

    for ineq, expected in expectations.items():
        actual = simplify_relational_set(ineq)
        assert actual == expected



