
from typing import Tuple

from sympy import Expr

from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference
from mpl.interpreter.expression_evaluation.entity_value import EntityValue


false_result = EntityValue()
true_result = EntityValue.from_value(1)


def query_negate(operand: EntityValue) -> EntityValue:
    match operand:
        case EntityValue() as x if x.value:
            return false_result
        case EntityValue():
            return true_result
        case x if x:
            return false_result
    return true_result


def target_and(op1: EntityValue, op2: EntityValue) -> EntityValue:
    """
    targets all references in op1 and op2
    """
    return op1 | op2


def target_xor(op1: EntityValue, op2: EntityValue) -> EntityValue:
    """
    this one is weird
    assuming an operand can have both references and values
    an operand is chosen when it has references and values, and its opposing operand lacks values
    else, nothing is chosen
    """

    one_refs = {x for x in op1.value if isinstance(x, Reference)}
    two_refs = {x for x in op2.value if isinstance(x, Reference)}
    one_vals = op1.value - one_refs
    two_vals = op2.value - two_refs

    if one_refs and not two_vals:
        return op1

    if two_refs and not one_vals:
        return op2

    return EntityValue()


def target_or(op1: EntityValue, op2: EntityValue) -> EntityValue:
    """
    assuming an operand can have both references and values
    any operand that has references, but not values is chosen
    """
    one_refs = {x for x in op1.value if isinstance(x, Reference)}
    two_refs = {x for x in op2.value if isinstance(x, Reference)}
    one_vals = op1.value - one_refs
    two_vals = op2.value - two_refs

    result = EntityValue()

    if one_refs and not one_vals:
        result |= op1

    if two_refs and not two_vals:
        result |= op2

    return result


def query_and(op1: EntityValue, op2: EntityValue) -> EntityValue:
    if op1 and op2:
        return op1 | op2

    return false_result


def query_or(op1: EntityValue, op2: EntityValue) -> EntityValue:
    if op1 or op2:
        return op1 | op2

    return false_result


def query_xor(op1: EntityValue, op2: EntityValue) -> EntityValue:
    if op1 and not op2:
        return op1

    if op2 and not op1:
        return op2

    return EntityValue()



quick_compare_dict = {
    '>': lambda x, y: x > y,
    '<': lambda x, y: x < y,
    '>=': lambda x, y: x >= y,
    '<=': lambda x, y: x <= y,
}


def eval_expr_with_context(expr: Expr, context: 'ContextTree') -> Tuple[EntityValue, EntityValue]:
    from symtable import Symbol
    out = EntityValue.from_value(expr)

    if expr.is_Symbol:
        ref = Reference.decode(expr)
        value = context[ref]
        return value, EntityValue.from_value({ref} | value.value)

    symbol: Symbol
    for symbol in map(str, expr.free_symbols):
        ref = Reference.decode(symbol)
        value = context[ref]
        out = simplify_expression_with_entity_value(out, str(symbol), value)
    return out.clean, EntityValue()


def simplify_expression_with_entity_value(source: EntityValue, symbol: str, value: EntityValue) -> EntityValue:
    from itertools import product
    from sympy import symbols

    substitutions = product(source.value, value.value)

    out = set()
    for item, replacement in substitutions:
        match item, replacement:
            case Expr(), str():
                v = item.subs(symbol, symbols(replacement))
                out.add(v)
            case Expr(), int() | float() | Expr():
                v = item.subs(symbol, replacement)
                out.add(v)
            case x, _:
                out.add(x)
    return EntityValue.from_value(out)



