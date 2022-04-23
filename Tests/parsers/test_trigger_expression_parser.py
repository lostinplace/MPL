from mpl.Parser.ExpressionParsers.reference_expression_parser import Ref
from mpl.Parser.ExpressionParsers.trigger_expression_parser import TriggerExpressionParsers as parser, TriggerExpression
from Tests import collect_parsing_expectations, quick_reference_expression as qre
from mpl.lib import fs


def test_trigger_expression_parsers():
    expectations = {
        "<test>": TriggerExpression(
            Ref("test").with_types('trigger').expression,
        ),
        "<Im a Complicated Event> With a Message:int": TriggerExpression(
            Ref('Im a Complicated Event', fs('trigger')).expression,
            source=None,
            messages=(qre('With a Message:int'),),
        ),
    }

    results = collect_parsing_expectations(expectations, parser.expression)
    for result in results:
        result = result.as_strings()
        assert result.actual == result.expected
