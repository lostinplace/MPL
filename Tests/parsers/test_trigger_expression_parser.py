from mpl.Parser.ExpressionParsers.trigger_expression_parser import TriggerExpressionParsers as parser, TriggerExpression
from Tests import collect_parsing_expectations, quick_reference_expression as qre


def test_trigger_expression_parsers():
    expectations = {
        "<test>": TriggerExpression(qre("test")),
        "<Im a Complicated Event> With a Message:int": TriggerExpression(
            qre("Im a Complicated Event"),
            source=None,
            messages=(qre('With a Message:int'),),
        ),
    }

    results = collect_parsing_expectations(expectations, parser.expression)
    for result in results:
        result = result.as_strings()
        assert result.actual == result.expected
