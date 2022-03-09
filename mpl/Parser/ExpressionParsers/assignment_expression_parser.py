from __future__ import annotations

import typing
from dataclasses import dataclass, replace

from parsita import TextParsers, longest

from mpl.Parser.ExpressionParsers.arithmetic_expression_parser \
    import ArithmeticExpression, ArithmeticExpressionParsers as ArExP
from mpl.Parser.ExpressionParsers.query_expression_parser \
    import QueryExpression, QueryExpressionParsers as QExP
from mpl.Parser.ExpressionParsers.reference_expression_parser \
    import ReferenceExpression, ReferenceExpressionParsers as RefExP
from mpl.Parser.Tokenizers.operator_tokenizers import AssignmentOperator, AssignmentOperatorParsers as AsOpP
from mpl.Parser.Tokenizers.simple_value_tokenizer import StringToken, SimpleValueTokenizers as svt


@dataclass(frozen=True, order=True)
class AssignmentExpression:
    lhs: ReferenceExpression
    rhs: ArithmeticExpression | QueryExpression | StringToken
    operator: AssignmentOperator

    def __str__(self) -> str:
        return f"{self.lhs} {self.operator} {self.rhs}"



default_assignment_expression = AssignmentExpression(None, None, None)


def interpret_to(default_dataclass, keys: typing.List[str]):
    def interpret_parser_results(parser_results):
        replacements = dict()
        for index, value in enumerate(parser_results):
            replacements[keys[index]] = value
        result = replace(default_dataclass, **replacements)
        return result
    return interpret_parser_results


class AssignmentExpressionParsers(TextParsers, whitespace=r'[ \t]*'):

    expression = RefExP.expression & AsOpP.operator & QExP.expression > \
                 interpret_to(default_assignment_expression, ['lhs', 'operator', 'rhs'])
