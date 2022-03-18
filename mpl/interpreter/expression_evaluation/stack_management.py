import itertools
from ast import literal_eval
from numbers import Number
from operator import itemgetter
from typing import Dict, List, Union, FrozenSet

from sympy import Expr

from mpl.Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpression
from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression
from mpl.Parser.ExpressionParsers.reference_expression_parser import ReferenceExpression, Reference
from mpl.Parser.ExpressionParsers.text_expression_parser import TextExpression
from mpl.Parser.ExpressionParsers.trigger_expression_parser import TriggerExpression
from mpl.Parser.Tokenizers.simple_value_tokenizer import NumberToken, StringToken
from mpl.interpreter.expression_evaluation.operators import OperatorOperation, OperationType, \
    query_operations_dict
from mpl.interpreter.expression_evaluation.types import symbolized_postfix_stack
from mpl.interpreter.expression_evaluation.types import postfix_stack
from mpl.lib.query_logic import MPL_Context, FinalResultSet, eval_expr_with_context


def get_postfix_operand(operand, operation_dict: Dict[str, OperatorOperation]):
    match operand:
        case ArithmeticExpression():
            return postfix(operand, operation_dict)
        case QueryExpression():
            return postfix(operand, operation_dict)
        case TextExpression():
            return operand.operands[0].content
        case NumberToken():
            return literal_eval(operand.content)
        case StringToken():
            return operand.content
        case ReferenceExpression():
            return operand.reference.without_types
        case TriggerExpression():
            return operand.name.reference


def flat_append(out: List, operand: str | Number | Reference | List):
    if isinstance(operand, list):
        out += operand
    else:
        out.append(operand)
    return out


def postfix(
        expression: QueryExpression | ArithmeticExpression,
        operation_dict: Dict[str, OperatorOperation]) -> postfix_stack:
    out = []
    stack = []
    operand = get_postfix_operand(expression.operands[0], operation_dict)
    flat_append(out, operand)

    for i, operator in enumerate(expression.operators):
        this_operator = operation_dict[operator.contents]
        operator_value = this_operator.score
        while stack and stack[-1][1] >= operator_value:
            out.append(stack.pop()[0])
        stack.append((this_operator, operator_value))
        if len(expression.operands) > i+1:
            operand = expression.operands[i + 1]
            operand = get_postfix_operand(operand, operation_dict)
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


def symbolize_expression(
        expression: QueryExpression,
        operations: Dict[str, OperatorOperation] = query_operations_dict) -> symbolized_postfix_stack:

    postfix_queue = postfix(expression, operations)
    symbolized = symbolize_postfix(postfix_queue)
    return tuple(symbolized)


def evaluate_symbolized_postfix_stack(
        postfix_queue: symbolized_postfix_stack,
        context: MPL_Context,
        target=False
) -> FinalResultSet:
    index = 0
    result: List[Union[Expr, OperatorOperation, FinalResultSet]] = list(postfix_queue)
    while index < len(result):
        item = result[index]
        match item:
            case Number() | str():
                result[index] = frozenset([item])
                index += 1
            case Expr():
                tmp = eval_expr_with_context(item, context, target)
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
                else:
                    raise Exception("Unhandled operation type")
                result[index - 2] = tmp
                del result[index - 1: index + 1]
                index -= 1

    assert len(result) == 1
    out = result[0]
    assert isinstance(out, FrozenSet)
    simplified = filter(bool, out)
    return frozenset(simplified)