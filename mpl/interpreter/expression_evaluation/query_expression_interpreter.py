import itertools
from numbers import Number
from operator import itemgetter
from typing import Collection, List, Union, FrozenSet

from sympy import Expr, simplify

from mpl.Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpression
from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression
from mpl.Parser.ExpressionParsers.reference_expression_parser import ReferenceExpression, Reference
from mpl.Parser.ExpressionParsers.trigger_expression_parser import TriggerExpression
from mpl.Parser.Tokenizers.simple_value_tokenizer import NumberToken, StringToken
from ast import literal_eval

from mpl.interpreter.expression_evaluation import OperatorOperation, op_dict
from mpl.interpreter.expression_evaluation.operators import OperationType
from mpl.lib.logic import MPL_Context, eval_expr_with_context, FinalResultSet


def get_postfix_operand(operand):
    match operand:
        case ArithmeticExpression():
            return postfix(operand)
        case QueryExpression():
            return postfix(operand)
        case NumberToken():
            return literal_eval(operand.content)
        case StringToken():
            return operand.content
        case ReferenceExpression():
            return operand.value
        case TriggerExpression():
            return operand.name


def flat_append(out: List, operand: str | Number | Reference | List):
    if isinstance(operand, Collection):
        out += operand
    else:
        out.append(operand)
    return out


postfix_stack = List[Union[Number, Reference, OperatorOperation]]
symbolized_postfix_stack = List[Union[Expr, OperatorOperation]]


def postfix(expression: QueryExpression | ArithmeticExpression) -> postfix_stack:
    out = []
    stack = []
    operand = get_postfix_operand(expression.operands[0])
    flat_append(out, operand)

    for i, operator in enumerate(expression.operators):
        this_operator = op_dict[operator.contents]
        operator_value = this_operator.score
        while stack and stack[-1][1] >= operator_value:
            out.append(stack.pop()[0])
        stack.append((this_operator, operator_value))
        if len(expression.operands) > i+1:
            operand = expression.operands[i + 1]
            operand = get_postfix_operand(operand)
            flat_append(out, operand)

    out += map(itemgetter(0), reversed(stack))
    return out


def symbolize_postfix(postfix_stack: postfix_stack) -> symbolized_postfix_stack:
    index = 0
    out_stack: symbolized_postfix_stack = []
    while index < len(postfix_stack):
        this_item = postfix_stack[index]
        match this_item:
            case Reference():
                out_stack.append(this_item.as_symbol())
            case OperatorOperation() if this_item.operation_type == OperationType.NumericAlgebra:
                    args = out_stack[-2:]
                    if all(isinstance(x, (Expr, Number)) for x in args):
                        result = this_item.method(*args)
                        out_stack = out_stack[0:-2] + [result]
                    else:
                        out_stack.append(this_item)
            case x:
                out_stack.append(x)
        index += 1
    return out_stack


def symbolize_expression(expression: QueryExpression) -> symbolized_postfix_stack:
    postfix_queue = postfix(expression)
    symbolized = symbolize_postfix(postfix_queue)
    return symbolized


def evaluate_symbolized_postfix_stack(postfix_queue: symbolized_postfix_stack, context: MPL_Context) -> FinalResultSet:
    index = 0
    result = postfix_queue.copy()
    while index < len(result):
        item = result[index]
        match item:
            case Number():
                result[index] = frozenset([item])
                index += 1
            case Expr():
                tmp = eval_expr_with_context(item, context)
                result[index] = tmp
                index += 1
            case OperatorOperation() if item.operation_type == OperationType.Unary:
                tmp = item.method(result[index - 1])
                result[index - 1] = tmp
                del result[index]
            case OperatorOperation():
                if item.operation_type == OperationType.Logical:
                    tmp = item.method(result[index - 2], result[index - 1])
                elif item.operation_type == OperationType.NumericAlgebra:
                    combinations = itertools.product(result[index - 2], result[index - 1])
                    tmp = map(lambda x: item.method(*x), combinations)
                    tmp = frozenset(tmp)
                result[index - 2] = tmp
                del result[index - 1: index + 1]
                index -= 1

    assert len(result) == 1
    out = result[0]
    assert isinstance(out, FrozenSet)
    simplified = filter(bool, out)
    return frozenset(simplified)
