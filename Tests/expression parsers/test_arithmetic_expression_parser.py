from Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpressionParsers
from Tests import assert_parsing_expectations, qdae, collect_parsing_expectations, qle



def test_simple_expression_parsers():
    expectations = {
        "2^((-1+6)/4)*7/-9/3": qdae(
            (2, '^'),
            (
                qdae(
                    (
                        qdae(
                            (-1, '+'),
                            6
                        ),
                        '/'
                    ),
                    4
                ),
                '*'
            ),
            (7, '/'),
            (-9, '/'),
            3,
        ),
        "(2-3)*4+-5.0^(6.12-0.7)": qdae(
            (
                qdae(
                    (2, '-'),
                    3
                ),
                '*'
            ),
            (4, '+'),
            (-5.0, '^'),
            qdae(
                (6.12, '-'),
                0.7
            )
        ),
        "1+(2-3)*4": qdae((1, '+'), (qdae((2, '-'), 3), '*'), 4),
        "1+(2-3)": qdae((1, '+'), ((2, '-'), 3)),
        "(1+2-3)": qdae((1, '+'), (2, '-'), 3),
        "0": qdae(0),
        "10": qdae(10),
        "-130.7": qdae(-130.7),
        "1+2": qdae((1, '+'), 2),
        "2-3*4": qdae((2, '-'), (3, '*'), 4),
        "12.0/-13^14.15--16": qdae((12.0, '/'), (-13, '^'), (14.15, '-'), -16),
    }

    for result in collect_parsing_expectations(expectations, ArithmeticExpressionParsers.expression):
        assert result.actual == result.expected


def test_simple_expression_parsers():
    expectations = {
        "1+(test-3)*4": qdae(
            (1, '+'),
            (qdae(
                (qle("test", 3), '-'),
                3
            ), '*'
            ),
            4
        ),
    }

    for result in collect_parsing_expectations(expectations, ArithmeticExpressionParsers.expression):
        assert result.actual == result.expected