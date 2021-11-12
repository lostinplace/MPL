from Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpression
from Parser.ExpressionParsers.machine_expression_parser import MachineDefinitionExpression
from Tests import collect_parsing_expectations, quick_parse


def test_machine_expression_parsers():
    expectations = {
        "%{10}": MachineDefinitionExpression(
            'a', []
        )
    }

    # results = collect_parsing_expectations(expectations, parser.expression)
    # for result in results:
    #     result = result.as_strings()
    #     assert result.actual == result.expected
