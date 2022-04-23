from parsita import Success

from mpl.Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpression
from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression, VectorExpression
from mpl.Parser.ExpressionParsers.scenario_expression_parser import ScenarioExpression, ScenarioExpressionParsers as parser
from Tests import collect_parsing_expectations, quick_parse


def test_scenario_expression_parsers():
    expectations = {
        "%{10}": ScenarioExpression(
            quick_parse(QueryExpression, '10')
        ),
        "%{aaron rodgers - 12}": ScenarioExpression(
            quick_parse(QueryExpression, 'aaron rodgers - 12')
        )
    }

    for expression, expected in expectations.items():
        actual = quick_parse(ScenarioExpression, expression)
        assert actual == expected


def test_vector_expression_parsers():
    expectations = {
        "{10}": VectorExpression(
            (quick_parse(QueryExpression, '10'),)
        ),
        "{aaron rodgers - 12}": VectorExpression(
            (quick_parse(QueryExpression, 'aaron rodgers - 12'),)
        )
    }

    for expression, expected in expectations.items():
        actual = quick_parse(VectorExpression, expression)
        assert actual == expected