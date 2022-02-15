from mpl.Parser.ExpressionParsers.query_expression_parser import Negation
from mpl.Parser.ExpressionParsers.reference_expression_parser import ReferenceExpression
from mpl.Parser.ExpressionParsers.state_expression_parser import StateExpressionParsers, StateExpression
from mpl.Parser.ExpressionParsers.trigger_expression_parser import TriggerExpression
from mpl.Parser.Tokenizers.operator_tokenizers import StateOperator
from Tests import collect_parsing_expectations, qre, quick_parse


def test_simple_state_expression_parsers():
    expectations = {
        'Smell Prey & !Feel Secure': StateExpression(
            (
                qre('Smell Prey'),
                Negation(qre('Feel Secure'))
            ),
            (StateOperator('&'),)
        ),
        "keep calm & !<kill> the messenger | be uninformed": StateExpression(
            (
                qre('keep calm'),
                Negation(
                    quick_parse(TriggerExpression, '<kill> the messenger')
                ),
                qre('be uninformed')
            ),
            (
                StateOperator('&'),
                StateOperator('|')
            )
        ),
        "*": StateExpression(
            (
                qre('void'),
            ),
            ()
        ),
        "state & <trigger>": StateExpression(
            (
                qre('state'),
                quick_parse(TriggerExpression, '<trigger>')
            ),
            (
                StateOperator('&'),
            )
        ),

        "end": StateExpression(
            (
                qre('end'),
            ),
            ()
        ),
        "!(a & b)": StateExpression(
            (
                Negation(
                    StateExpression(
                        (
                            qre('a'),
                            qre('b')
                        ),
                        (
                            StateOperator('&'),
                        )
                    )
                ),
            ),
            ()
        ),
        "!c:STATE": StateExpression(
            (Negation( qre('c:STATE')),),
            (),
        ),
        "test one:me & !c:STATE | d": StateExpression(
            (
                qre('test one:me'),
                Negation(
                    quick_parse(ReferenceExpression, 'c:STATE')
                ),
                qre('d'),
            ),
            (
                StateOperator('&'),
                StateOperator('|')
            )
        ),
        "d & e": StateExpression(
            (qre('d'), qre('e')),
            (StateOperator('&'),)
        ),
        "test two:again|g:STATE": StateExpression(
            (
                qre('test two:again'),
                qre('g:STATE'),
            ),
            (StateOperator('|'),)
        )
    }

    results = collect_parsing_expectations(expectations, StateExpressionParsers.expression)
    for result in results:
        result = result.as_strings()
        assert result.actual == result.expected
