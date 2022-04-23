from symtable import Symbol
from typing import FrozenSet, Optional

from sympy import symbols, And
from sympy.core.numbers import oo
from sympy.core.relational import Relational, Eq, _Inequality
from sympy.logic.boolalg import BooleanFalse

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



