from dataclasses import dataclass
from typing import Union, List

from parsita import TextParsers, fwd, opt

from Parser.ExpressionParsers.label_expression_parser import LabelExpression, LabelExpressionParsers as lep
from Parser.Tokenizers.operator_tokenizers import StateOperator, StateOperatorParsers as sop
from lib.CustomParsers import best, repwksep


@dataclass(frozen=True, order=True)
class StateOperation:
    operand: Union[LabelExpression, 'StateExpression']
    operator: StateOperator


@dataclass(frozen=True, order=True)
class StateExpression:
    operations: List[StateOperation]


# TODO: Continue here

def get_operand(parser_result_component):
    if parser_result_component[0]:
        result = StateExpression([
            StateOperation(
                parser_result_component[1],
                parser_result_component[0][0]
            )
        ])
    else:
        result = parser_result_component[1]
    return result


def interpret_simple_expression(parser_results):
    operations = []
    for parser_result in parser_results:
        if isinstance(parser_result, tuple):
            operand = parser_result[0]
            operator = parser_result[1]
        elif isinstance(parser_result, list) and parser_result[0] == StateOperator('!'):
            operand = parser_result[1]
            operator = parser_result[0]
        else:
            operand = parser_result
            operator = None

        tmp = StateOperation(operand, operator)
        operations.append(tmp)
    result = StateExpression(operations)
    return result


class StateExpressionParsers(TextParsers):
    simple_expression = fwd()
    parenthesized_simple_expression = '(' >> simple_expression << ')'

    simple_expression_operand = lep.expression | parenthesized_simple_expression
    negated_simple_expression_operand = sop.not_state & simple_expression_operand
    __tmp_se = repwksep((simple_expression_operand | negated_simple_expression_operand), (sop.and_state | sop.or_state)) > interpret_simple_expression
    simple_expression.define(__tmp_se)

    expression = best(parenthesized_simple_expression | simple_expression)
