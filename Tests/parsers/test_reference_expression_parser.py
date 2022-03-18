from parsita import Success

from mpl.Parser.ExpressionParsers.reference_expression_parser import ReferenceExpressionParsers, ReferenceExpression, \
    Reference
from Tests import collect_parsing_expectations
from mpl.lib import fs


def test_reference_expression_parsers():
    expectations = {
        "a": ReferenceExpression(
            ('a',),
            None
        ),
        "a:test": ReferenceExpression(
            ('a',),
            fs('test')
        ),
        "Wumpus: machine": ReferenceExpression(
            ('Wumpus',),
            fs('machine')
        ),
        "Ok: Health": ReferenceExpression(
            ('Ok',),
            fs('Health')
        ),
        "Health.Ok.Treatment:state": ReferenceExpression(
            ('Health', 'Ok', 'Treatment'),
            fs('state')
        ),
    }

    for expression, expected in expectations.items():
        actual = ReferenceExpressionParsers.expression.parse(expression)
        assert actual == Success(expected), expression

