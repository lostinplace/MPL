from Parser.ExpressionParsers.reference_expression_parser import Reference
from Parser.ExpressionParsers.trigger_expression_parser import TriggerExpressionParsers as parser, TriggerExpression
from Tests import collect_parsing_expectations, qre, qdae


def test_trigger_expression_parsers():
    expectations = {
        "<test>": TriggerExpression(Reference('test', 'trigger'), None),
        "<Im a Complicated Event> With a Message:int": TriggerExpression(
            Reference('Im a Complicated Event', 'trigger'),
            qre('With a Message:int')
        ),
    }

    results = collect_parsing_expectations(expectations, parser.expression)
    for result in results:
        result = result.as_strings()
        assert result.actual == result.expected
