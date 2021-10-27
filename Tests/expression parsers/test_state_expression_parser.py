from Parser.ExpressionParsers.state_expression_parser import StateExpressionParsers, StateOperation, StateExpression
from Parser.Tokenizers.operator_tokenizers import StateOperator
from Tests import collect_parsing_expectations, qle


def test_simple_state_expression_parsers():
    expectations = {
        "END": StateExpression([
            StateOperation(
                qle('END'),
                None
            ),
        ]),
        "VOID": StateExpression([
            StateOperation(
                qle('VOID'),
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
        "!c:STATE": StateExpression([
            StateOperation(
                qle('c:STATE', 1),
                StateOperator('!')
            ),
        ]),
        "test one:me & !c:STATE | d": StateExpression([
            StateOperation(
                qle('test one:me'),
                StateOperator('&')
            ),
            StateOperation(
                StateExpression([
                    StateOperation(
                        qle('c:STATE', 15),
                        StateOperator('!')
                    )
                ]),
                StateOperator('|')
            ),
            StateOperation(
                qle('d', 25),
                None
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
    for result in results:
        result = result.as_strings()
        assert result.actual == result.expected
