from Parser.ExpressionParsers.reference_expression_parser import ReferenceExpressionParsers, ReferenceExpression, \
    Reference
from Parser.Tokenizers.simple_value_tokenizer import ReferenceToken
from Tests import collect_parsing_expectations


def test_reference_expression_parsers():
    expectations = {
        "a": ReferenceExpression(
           Reference('a', None),
           []
        ),
        "a:test": ReferenceExpression(
            Reference('a',  ReferenceToken("test")),
            []
        ),
        "Wumpus: machine": ReferenceExpression(
            Reference('Wumpus', ReferenceToken("machine")),
            []
        ),
        "Ok: Health": ReferenceExpression(
            Reference('Ok', ReferenceToken("Health")),
            []
        ),
        "//Health:state/Ok/Treatment:state": ReferenceExpression(
            Reference('Treatment', ReferenceToken("state")),
            [
                Reference('Ok', None),
                Reference('Health', ReferenceToken("state")),
            ]
        ),
    }

    for result in collect_parsing_expectations(expectations, ReferenceExpressionParsers.expression):
        result = result.as_strings()
        assert result.actual == result.expected


