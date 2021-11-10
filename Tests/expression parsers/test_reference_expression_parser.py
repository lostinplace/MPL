from Parser.ExpressionParsers.reference_expression_parser import ReferenceExpressionParsers, ReferenceExpression, \
    Reference
from Parser.Tokenizers.simple_value_tokenizer import ReservedToken, ReferenceToken
from Tests import collect_parsing_expectations


def test_reference_expression_parsers():
    expectations = {
        "a": ReferenceExpression(
           Reference('a', None),
           []
        ),
        "a:TEST": ReferenceExpression(
            Reference('a',  ReservedToken("TEST")),
            []
        ),
        "Wumpus: MACHINE": ReferenceExpression(
            Reference('Wumpus', ReservedToken("MACHINE")),
            []
        ),
        "Ok: Health": ReferenceExpression(
            Reference('Ok', ReferenceToken("Health")),
            []
        ),
        "Health:STATE/Ok/Treatment:STATE": ReferenceExpression(
            Reference('Treatment', ReservedToken("STATE")),
            [
                Reference('Ok', None),
                Reference('Health', ReservedToken("STATE")),
            ]
        ),
    }

    for result in collect_parsing_expectations(expectations, ReferenceExpressionParsers.expression):
        result = result.as_strings()
        assert result.actual == result.expected


