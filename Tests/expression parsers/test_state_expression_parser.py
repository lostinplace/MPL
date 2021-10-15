from Parser.ExpressionParsers.state_expression_parser import StateExpressionParsers, StateOperation, StateExpression
from Parser.Tokenizers.operator_tokenizers import StateOperator
from Tests import collect_parsing_expectations, qle



def test_simple_expression_parsers():
    expectations = {
        "test one:me & !c:STATE": StateExpression([
            StateOperation(
                qle('test one:me'),
                StateOperator('&')
            ),
            StateOperation(
                StateExpression([
                    StateOperation(
                        qle('c:STATE', 14),
                        StateOperator('!')
                    )
                ]),
                None
            ),
        ]),
        "!(a & b)": StateExpression([
            StateOperation(
                StateExpression([
                    StateOperation(qle('a', 2), StateOperator('&')),
                    StateOperation(qle('b', 6), None)
                ]),
                StateOperator('!')
            ),
        ]),
        "d & e": StateExpression([
            StateOperation(
                qle('d'),
                StateOperator('&')
            ),
            StateOperation(
                qle('e', 4),
                None
            ),
        ]),
        "test two:again|g:STATE": StateExpression([
            StateOperation(
                qle('test two:again'),
                StateOperator('|')
            ),
            StateOperation(
                qle('g:STATE', 15),
                None
            ),
        ]),
    }

    results = collect_parsing_expectations(expectations, StateExpressionParsers.expression)
    for actual, expected, input in results:
        assert actual == expected
