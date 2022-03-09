from __future__ import annotations

from dataclasses import dataclass
from itertools import zip_longest
from typing import Union, Tuple

from parsita import TextParsers, fwd, longest

from mpl.Parser.ExpressionParsers.reference_expression_parser import ReferenceExpression, ReferenceExpressionParsers as lexp
from mpl.Parser.Tokenizers.operator_tokenizers import ArithmeticOperator, ArithmeticOperatorParsers as aop
from mpl.Parser.Tokenizers.simple_value_tokenizer import NumberToken, SimpleValueTokenizers as svt, StringToken
from mpl.lib.parsers.repsep2 import repsep2


@dataclass(frozen=True, order=True)
class TextExpression:
    operands: Tuple[StringToken, ...]
    operators: Tuple[ArithmeticOperator, ...]

    def __str__(self):
        result = ''
        for operand, operator in zip_longest(self.operands, self.operators):
            result += str(operand)
            if operator is not None:
                result += str(operator)
        return result

def interpret_simple_expression(parser_results):
    operands = tuple(parser_results)
    operators = parser_results.separators

    result = TextExpression(operands, operators)
    return result


class TextExpressionParsers(TextParsers, whitespace=r'[ \t]*'):
    text_expression_operand = svt.string_token
    expression = repsep2(text_expression_operand, aop.operator, min=1) > interpret_simple_expression

