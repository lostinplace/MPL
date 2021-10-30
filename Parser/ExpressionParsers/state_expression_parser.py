from dataclasses import dataclass
from typing import Union, List

from parsita import TextParsers, fwd, opt, lit

from Parser.ExpressionParsers.label_expression_parser import LabelExpression, LabelExpressionParsers as lep
from Parser.Tokenizers.operator_tokenizers import StateOperator, StateOperatorParsers as sop
from lib.CustomParsers import best, repwksep, repsep2, SeparatedList


@dataclass(frozen=True, order=True)
class StateOperation:
    operand: Union[LabelExpression, 'StateExpression']
    operator: StateOperator


@dataclass(frozen=True, order=True)
class StateExpression:
    operations: List[StateOperation]


def interpret_negated_expression(parser_result):
    operand = parser_result[1]
    operator = parser_result[0]
    operation = StateOperation(operand, operator)
    result = StateExpression([operation])
    return result


def interpret_simple_expression(parser_results: SeparatedList):
    operands = parser_results
    operators = parser_results.separators + [None]

    operations = [StateOperation(operand, operator) for operand, operator in  zip(operands, operators)]

    result = StateExpression(operations)
    return result


class StateExpressionParsers(TextParsers):
    simple_expression = fwd()
    parenthesized_simple_expression = '(' >> simple_expression << ')'

    negated_expression = sop.not_state & (lep.expression | parenthesized_simple_expression) > interpret_negated_expression

    simple_expression_operand = parenthesized_simple_expression | negated_expression | lep.expression

    __tmp_se = repsep2(
        simple_expression_operand,
        (sop.and_state | sop.or_state),
        min=1
    ) > interpret_simple_expression

    simple_expression.define(__tmp_se)

    expression = negated_expression | simple_expression
