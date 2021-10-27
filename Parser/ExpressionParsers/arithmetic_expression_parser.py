from dataclasses import dataclass
from typing import Union, List

from parsita import TextParsers, fwd, longest

from Parser.ExpressionParsers.label_expression_parser import LabelExpression
from Parser.Tokenizers.operator_tokenizers import ArithmeticOperator, ArithmeticOperatorParsers as aop
from Parser.Tokenizers.simple_value_tokenizer import NumberToken, SimpleValueTokenizers as svp
from lib.CustomParsers import best, repwksep, repsep2


@dataclass(frozen=True, order=True)
class ArithmeticOperation:
    operand: Union[NumberToken, LabelExpression, 'ArithmeticExpression']
    operator: ArithmeticOperator


@dataclass(frozen=True, order=True)
class ArithmeticExpression:
    operations: List[ArithmeticOperation]


def interpret_simple_expression(parser_results):
    operands = parser_results
    operators = parser_results.separators + [None]

    operations = [ArithmeticOperation(operand, operator) for operand, operator in  zip(operands, operators)]

    result = ArithmeticExpression(operations)
    return result


class ArithmeticExpressionParsers(TextParsers):
    simple_expression = fwd()
    parenthesized_simple_expression = '(' >> simple_expression << ')'

    simple_expression_operand = svp.number_token | parenthesized_simple_expression
    __tmp_se = repsep2(simple_expression_operand, aop.operator) > interpret_simple_expression
    simple_expression.define(__tmp_se)

    expression = longest(parenthesized_simple_expression, simple_expression )
