from Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpressionParsers, ArithmeticExpression
from Parser.ExpressionParsers.reference_expression_parser import ReferenceExpression
from Parser.Tokenizers.operator_tokenizers import ArithmeticOperator
from Parser.Tokenizers.simple_value_tokenizer import NumberToken
from Tests import qdae, collect_parsing_expectations, qre


def test_simple_expression_parsers():
    expectations = {
        "2^((-1+6)/4)*7/-9/3": ArithmeticExpression(
            (
                NumberToken("2"),
                ArithmeticExpression(
                    (
                        ArithmeticExpression(
                            (NumberToken("-1"), NumberToken("6")),
                            (ArithmeticOperator("+"),)
                        ),
                        NumberToken("4")
                    ),
                    (ArithmeticOperator("/"),)
                ),
                NumberToken("7"),
                NumberToken("-9"),
                NumberToken("3"),
            ),
            (
                ArithmeticOperator("^"),
                ArithmeticOperator("*"),
                ArithmeticOperator("/"),
                ArithmeticOperator("/"),
            )
        ),
        "(2-3)*4+-5.0^(6.12-0.7)": ArithmeticExpression(
            (
                ArithmeticExpression(
                    (NumberToken("2"), NumberToken("3")),
                    (ArithmeticOperator('-'),),
                ),
                NumberToken("4"),
                NumberToken("-5.0"),
                ArithmeticExpression(
                    (NumberToken("6.12"), NumberToken("0.7")),
                    (ArithmeticOperator('-'),),
                ),
            ),
            (
                ArithmeticOperator("*"),
                ArithmeticOperator("+"),
                ArithmeticOperator("^"),
            )
        ),
        "0": ArithmeticExpression((NumberToken("0"),), ()),
        "10": ArithmeticExpression((NumberToken("10"),), ()),
        "-130.7": ArithmeticExpression((NumberToken("-130.7"),), ()),
        "1+2": ArithmeticExpression(
            (NumberToken("1"), NumberToken("2")),
            (ArithmeticOperator("+"),),
        ),
        "12.0/-13^14.15--16": ArithmeticExpression(
            (
                NumberToken("12.0"),
                NumberToken("-13"),
                NumberToken("14.15"),
                NumberToken("-16"),
            ),
            (
                ArithmeticOperator("/"),
                ArithmeticOperator("^"),
                ArithmeticOperator("-"),
            )
        ),
    }

    for result in collect_parsing_expectations(expectations, ArithmeticExpressionParsers.expression):
        result = result.as_strings()
        assert result.actual == result.expected


def test_simple_expression_parsers_with_references():
    expectations = {
        "1+(test-3)*4": ArithmeticExpression(
            (
                NumberToken("1"),
                ArithmeticExpression(
                    (qre("test"), NumberToken("3")),
                    (ArithmeticOperator("-"),)
                ),
                NumberToken("4")
            ),
            (ArithmeticOperator("+"), ArithmeticOperator("*"))
        ),
    }

    for result in collect_parsing_expectations(expectations, ArithmeticExpressionParsers.expression):
        assert result.actual == result.expected