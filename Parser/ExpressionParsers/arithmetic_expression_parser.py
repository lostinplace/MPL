from dataclasses import dataclass
from typing import Union, List

from parsita import TextParsers, fwd, rep1sep, repsep
from parsita.util import splat

from Parser.ExpressionParsers.label_expression_parser import LabelExpression
from Parser.Tokenizers.operator_tokenizers import ArithmeticOperator, ArithmeticOperatorParsers as aop
from Parser.Tokenizers.simple_value_tokenizer import NumberToken, SimpleValueTokenizers as svp
from lib.CustomParsers import best, repwksep


@dataclass(frozen=True, order=True)
class ArithmeticOperation:
    operand: Union[NumberToken, LabelExpression, 'ArithmeticExpression']
    operator: ArithmeticOperator


@dataclass(frozen=True, order=True)
class ArithmeticExpression:
    operations: List[ArithmeticOperation]


def interpret_simple_expression(parser_results):
    operations = []
    for parser_result in parser_results:
        operand = parser_result
        operator = None
        if isinstance(parser_result, tuple):
            operand = parser_result[0]
            operator = parser_result[1]
        tmp = ArithmeticOperation(operand, operator)
        operations.append(tmp)
    result = ArithmeticExpression(operations)
    return result


class ArithmeticExpressionParsers(TextParsers):
    simple_expression = fwd()
    parenthesized_simple_expression = '(' >> simple_expression << ')'

    simple_expression_operand = svp.number_token | parenthesized_simple_expression
    __tmp_se = repwksep(simple_expression_operand, aop.operator) > interpret_simple_expression
    simple_expression.define(__tmp_se)

    expression = best(parenthesized_simple_expression | simple_expression )
