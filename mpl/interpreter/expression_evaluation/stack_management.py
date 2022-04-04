from ast import literal_eval
from numbers import Number
from operator import itemgetter
from typing import Dict, List

from sympy import Expr, Symbol
from sympy.core.relational import Relational

from mpl.Parser.ExpressionParsers import Expression
from mpl.Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpression
from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression
from mpl.Parser.ExpressionParsers.reference_expression_parser import ReferenceExpression, Reference
from mpl.Parser.ExpressionParsers.text_expression_parser import TextExpression
from mpl.Parser.ExpressionParsers.trigger_expression_parser import TriggerExpression
from mpl.Parser.Tokenizers.simple_value_tokenizer import NumberToken, StringToken
from mpl.interpreter.expression_evaluation.entity_value import EntityValue
from mpl.interpreter.expression_evaluation.operators import OperatorOperation, OperationType, \
    query_operations_dict
from mpl.interpreter.expression_evaluation.types import symbolized_postfix_stack
from mpl.interpreter.expression_evaluation.types import postfix_stack
from mpl.lib.query_logic.expression_processing import entity_value_from_expression, simplify_entity_value


def get_postfix_operand(operand: Expression, operation_dict: Dict[str, OperatorOperation]):
    match operand:
        case ArithmeticExpression() as x:
            return postfix(x, operation_dict)
        case QueryExpression() as x:
            return postfix(x, operation_dict)
        case TextExpression() as x:
            return Symbol(f'`{x.operands[0].content}`')
        case NumberToken() as x:
            return literal_eval(x.content)
        case StringToken() as x:
            return Symbol(f'`{x.content}`')
        case ReferenceExpression() as x:
            return x.reference.without_types
        case TriggerExpression() as x:
            return x.name.reference


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


def symbolize_postfix(postfix_order_stack: postfix_stack) -> symbolized_postfix_stack:
    index = 0
    out_stack = []
    while index < len(postfix_order_stack):
        this_item = postfix_order_stack[index]
        match this_item:
            case Reference():
                out_stack.append(this_item.symbol)
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
    return tuple(out_stack)


def symbolize_expression(
        expression: QueryExpression,
        operations: Dict[str, OperatorOperation] = query_operations_dict) -> symbolized_postfix_stack:

    postfix_queue = postfix(expression, operations)
    symbolized = symbolize_postfix(postfix_queue)
    return tuple(symbolized)


#TODO: test this to ensure it works
def evaluate_symbolized_postfix_stack(
        postfix_queue: symbolized_postfix_stack,
        context: 'EngineContext',
) -> EntityValue:

    index: int = 0
    result: List[int | str | Expr | EntityValue | OperatorOperation] = list(postfix_queue)

    while index < len(result):
        item = result[index]
        match item:
            case Number() | str():
                result[index] = EntityValue.from_value(item)
                index += 1
            case Expr() | Relational():
                tmp = entity_value_from_expression(item, context)
                result[index] = tmp
                index += 1
            case OperatorOperation() if item.operation_type == OperationType.Unary:
                tmp = item.method(result[index - 1])
                result[index - 1] = tmp
                del result[index]
            case OperatorOperation():
                tmp = item.method(result[index - 2], result[index - 1])
                result[index - 2] = tmp
                del result[index - 1: index + 1]
                index -= 1

    assert len(result) == 1
    out = result[0]
    assert isinstance(out, EntityValue)
    out = out.clean
    out = simplify_entity_value(out, context)
    return out