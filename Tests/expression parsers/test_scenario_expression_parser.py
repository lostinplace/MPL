from Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpression
from Parser.ExpressionParsers.scenario_expression_parser import ScenarioExpression, ScenarioExpressionParsers as parser
from Tests import collect_parsing_expectations, quick_parse


def test_scenario_expression_parsers():
    expectations = {
        "%{10}": ScenarioExpression(
            quick_parse(ArithmeticExpression, '10')
        ),
        "%{aaron rodgers - 12}": ScenarioExpression(
            quick_parse(ArithmeticExpression, 'aaron rodgers - 12')
        )
    }

    results = collect_parsing_expectations(expectations, parser.expression)
    for result in results:
        result = result.as_strings()
        assert result.actual == result.expected
