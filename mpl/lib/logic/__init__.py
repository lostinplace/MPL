from itertools import product
from numbers import Number
from typing import FrozenSet, Union, Dict, Set

from sympy import Expr, symbols, Symbol

from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference
from mpl.interpreter.reference_resolution.reference_graph_resolution import MPLEntity


MPLContext = Dict[Reference, Union[Number, str, Expr, MPLEntity]]

ValueType = Union[str, Number, Expr, Symbol]

LogicalResult = FrozenSet[ValueType]


false_result = frozenset()

simple_true_result = frozenset([1])


def logic_negate(operand: LogicalResult) -> LogicalResult:
    match operand:
        case MPLEntity() as x if x.value:
            return false_result
        case MPLEntity():
            return simple_true_result
        case x if x:
            return false_result
    return simple_true_result


def logic_and(*operands: LogicalResult) -> LogicalResult:
    result:  LogicalResult
    if operands[0]:
        result = operands[0]
    else:
        return false_result

    for operand in operands[1:]:
        if not operand:
            return false_result
        result |= operand

    return result


def logic_or(*operands: LogicalResult) -> LogicalResult:
    result:  LogicalResult = frozenset()

    for operand in operands:
        result |= operand

    return result


def logic_xor(*operands: LogicalResult) -> LogicalResult:
    result:  LogicalResult = frozenset()

    for operand in operands:
        if not operand:
            continue

        if result:
            return false_result

        result = operand
    return result


def equivalent_intersection(left: LogicalResult, right: LogicalResult) -> LogicalResult:
    out = set()
    combinations = set(product(left, right))
    for item, item_2 in combinations:
        match item, item_2:
            case Number() | Expr() as x, Number() | Expr() as y:
                result = x == y
            case MPLEntity() as x, MPLEntity() as y:
                result = logic_eq(x.value, y.value)
            case MPLEntity() as x, y:
                result = logic_eq(x.value, frozenset([y]))
            case x, MPLEntity() as y:
                result = logic_eq(y.value, frozenset([x]))
        if result:
            out |= {item, item_2}
    return out


def logic_eq(left: LogicalResult, right: LogicalResult) -> LogicalResult:
    if len(left) != len(right):
        return false_result
    out = equivalent_intersection(left, right)
    if right.issubset(out) and left.issubset(out):
        return out
    return false_result


def logic_neq(left: LogicalResult, right: LogicalResult) -> LogicalResult:
    tmp = equivalent_intersection(left, right)
    result = (left | right) - tmp
    return result


quick_compare_dict = {
    '>': lambda x, y: x > y,
    '<': lambda x, y: x < y,
    '>=': lambda x, y: x >= y,
    '<=': lambda x, y: x <= y,
}


def logic_inequality_compare(left: LogicalResult, right: LogicalResult, comparator) -> LogicalResult:
    if not left or not right:
        comparison_result = comparator(len(left), len(right))
        if comparison_result and left:
            return left
        elif comparison_result and not left:
            return simple_true_result

    combinations = set(product(left, right))
    out = set()
    for left_single, right_single in combinations:
        result = None
        match left_single, right_single:
            case Number() as x, Number() as y:
                result = comparator(x, y)
            case Expr() | Number() as x, Expr() | Number() as y:
                out.add(comparator(x, y))
                continue
            case MPLEntity() as x, MPLEntity() as y:
                result = logic_inequality_compare(x.value, y.value, comparator)
            case MPLEntity() as x, y:
                result = logic_inequality_compare(x.value, set([y]), comparator)
            case x, MPLEntity() as y:
                result = logic_inequality_compare(set([x]), y.value, comparator)

        if result:
            out.add(x)
        else:
            return false_result
    return frozenset(out)


def logic_gt(left: LogicalResult, right: LogicalResult) -> LogicalResult:
    return logic_inequality_compare(left, right, quick_compare_dict['>'])


def logic_lt(left: LogicalResult, right: LogicalResult) -> LogicalResult:
    return logic_inequality_compare(left, right, quick_compare_dict['<'])


def logic_ge(left: LogicalResult, right: LogicalResult) -> LogicalResult:
    return logic_inequality_compare(left, right, quick_compare_dict['>='])


def logic_le(left: LogicalResult, right: LogicalResult) -> LogicalResult:
    return logic_inequality_compare(left, right, quick_compare_dict['<='])


MPL_Context = Dict[Reference, Union[Number, str, Expr, MPLEntity]]

OpResult = Union[Expr, Number, str, MPLEntity]

ResultSet = Set[OpResult]

FinalResultSet = FrozenSet[OpResult]


def eval_expr_with_context(expr: Expr, context: MPL_Context) -> FinalResultSet:
    out = set([expr])

    if isinstance(expr, Symbol):
        ref = Reference.decode(expr)
        value = context.get(ref)
        if isinstance(value, MPLEntity):
            if value.value:
                return frozenset([value])
            else:
                return frozenset()

    for symbol in map(str, expr.free_symbols):
        ref = Reference.decode(symbol)
        value = context.get(ref)
        match value:
            case int() | float() | str() | Expr():
                out = simplify_result_set(out, symbol, {value})
            case MPLEntity() as x if x.value:
                out = simplify_result_set(out, symbol, x.value)
            case frozenset():
                out = simplify_result_set(out, symbol, value)
            case MPLEntity():
                out = simplify_result_set(out, symbol, set())
    no_zeroes = filter(bool, out)
    return frozenset(no_zeroes)


def simplify_result_set(input: ResultSet, symbol:str, values: ResultSet) -> ResultSet:
    from itertools import product
    substitutions = product(input, values)

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
    return out



