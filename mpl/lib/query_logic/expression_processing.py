
# an EntityValue can contain expressions with symbols
# those symbols are either references to other EntityValues, or plain symbols
# if an expression has only symbols that refer to plain symbols, then it is simplified
# an entity value is simplified when all of its symbols refer to plain symbols
from typing import FrozenSet, Set

from sympy import Expr, Symbol, symbols
from sympy.core.relational import Relational

from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference
from mpl.interpreter.expression_evaluation.engine_context import EngineContext
from mpl.interpreter.expression_evaluation.entity_value import EntityValue, ev_fv


def expr_set_is_simplified(exprs: FrozenSet[Expr], context: EngineContext) -> bool:
    tmp = ev_fv(exprs)
    return ev_is_simplified(tmp, context)


# an expression is simplified when all oof it's decoded free symbols are symbols from the context
def expression_is_simplified(expr: Expr, context: EngineContext) -> bool:
    tmp = ev_fv(expr)
    return ev_is_simplified(tmp, context)


def ev_is_simplified(value: EntityValue, context: 'EngineContext') -> bool:
    ev_symbols = value.free_symbols
    ev_symbols = frozenset(
        [
            x for x in ev_symbols
            if not ('`' in str(x))
        ]
    )
    engine_symbols = context.symbols
    return ev_symbols.issubset(engine_symbols) or not ev_symbols


def get_free_symbols(value: Set[Expr]) -> FrozenSet[Symbol]:
    result = set()
    for x in value:
        result |= x.free_symbols
    return frozenset(result)


def subs_expr_symbol_with_multiple_values(expr: Expr, symbol: Symbol, values: EntityValue) -> FrozenSet[Expr]:
    result = set()
    for value in values:
        if isinstance(value, str):
            # TODO: this is wrong, we should be able to handle strings as well
            value = Symbol(f'`{value}`')
        tmp = expr.subs(symbol, value)
        result.add(tmp)
    return frozenset(result)


def simplify_single_expression(expr: Expr | Relational, context: EngineContext) -> FrozenSet[Expr]:
    result = set()
    working_set = {expr}
    while working_set:
        this_expression = working_set.pop()
        if isinstance(this_expression, Symbol) and '`' not in str(this_expression):
            result.add(Reference.decode(this_expression))
        for symbol in this_expression.free_symbols:
            ref = Reference.decode(symbol)
            value = context[ref]

            value_refs = value.references
            result |= value_refs
            value = value.value - value_refs

            if symbol in context.symbols and not value:
                # if it's a symbol that is marked as symbol in context, and it has no value,
                # then it can be left alone
                continue

            if '`' in str(symbol):
                # ignore string entirely ( for now )
                continue

            if value:
                tmp_results = subs_expr_symbol_with_multiple_values(this_expression, symbol, value)
                as_list = list(tmp_results)
                this_expression, remainders = as_list[0], as_list[1:]
                working_set |= set(remainders)
            else:
                this_expression = this_expression.subs(symbol, 0)

        if expression_is_simplified(this_expression, context):
            result.add(this_expression)
        else:
            working_set.add(this_expression)
    return frozenset(result)


def entity_value_from_expression(expr: Expr | Relational, context: EngineContext) -> EntityValue:
    result = simplify_single_expression(expr, context)
    return EntityValue(result).clean


def simplify_entity_value(value: EntityValue, context: EngineContext) -> EntityValue:
    result = EntityValue()
    for v in value:
        if isinstance(v, Expr):
            result |= entity_value_from_expression(v, context)
        else:
            result |= v
    return result
