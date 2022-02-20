from mpl.Parser.ExpressionParsers.reference_expression_parser import ReferenceExpressionParsers, ReferenceExpression, \
    Reference
from Tests import collect_parsing_expectations


def test_reference_expression_parsers():
    expectations = {
        "a": ReferenceExpression(
            Reference('a', None),
            ()
        ),
        "a:test": ReferenceExpression(
            Reference('a', "test"),
            ()
        ),
        "Wumpus: machine": ReferenceExpression(
            Reference('Wumpus', "machine"),
            ()
        ),
        "Ok: Health": ReferenceExpression(
            Reference('Ok', "Health"),
            ()
        ),
        "//Health:state/Ok/Treatment:state": ReferenceExpression(
            Reference('Treatment', "state"),
            (
                Reference('Ok', None),
                Reference('Health', "state"),
            )
        ),
    }

    for result in collect_parsing_expectations(expectations, ReferenceExpressionParsers.expression):
        result = result.as_strings()
        assert result.actual == result.expected


