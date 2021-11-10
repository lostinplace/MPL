from Parser.ExpressionParsers.state_expression_parser import StateExpressionParsers, StateOperation, StateExpression
from Parser.Tokenizers.operator_tokenizers import StateOperator
from Tests import collect_parsing_expectations, qre


def test_simple_state_expression_parsers():
    expectations = {
        "END": StateExpression(
            [qre('END')], []
        ),
        "VOID": StateExpression(
            [qre('VOID')],
            []
        ),
        "!(a & b)": StateExpression(
            [
                StateExpression(
                    [
                        qre('a'),
                        qre('b')
                    ],
                    [
                        StateOperator('&')
                    ]
                )
            ],
            [
                StateOperator('!')
            ]
        ),

        "!c:STATE": StateExpression(
            [qre('c:STATE')],
            [StateOperator('!')]
        ),
        "test one:me & !c:STATE | d": StateExpression(
            [
                qre('test one:me'),
                StateExpression(
                    [qre('c:STATE')],
                    [StateOperator('!')]
                ),
                qre('d'),
            ],
            [
                StateOperator('&'),
                StateOperator('|')
            ]
        ),
        "d & e": StateExpression(
            [qre('d'), qre('e')],
            [StateOperator('&')]
        ),
        "test two:again|g:STATE": StateExpression(
            [
                qre('test two:again'),
                qre('g:STATE'),
            ],
            [ StateOperator('|') ]
        )
    }

    results = collect_parsing_expectations(expectations, StateExpressionParsers.expression)
    for result in results:
        result = result.as_strings()
        assert result.actual == result.expected
