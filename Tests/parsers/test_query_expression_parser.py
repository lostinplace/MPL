from typing import Any

from mpl.Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpression
from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression, \
    QueryExpressionParsers

from Tests import collect_parsing_expectations, qre, qdae, quick_parse
from mpl.Parser.ExpressionParsers.text_expression_parser import TextExpression
from mpl.Parser.ExpressionParsers.trigger_expression_parser import TriggerExpression
from mpl.Parser.Tokenizers.operator_tokenizers import QueryOperator, ArithmeticOperator
from mpl.Parser.Tokenizers.simple_value_tokenizer import StringToken


def qne(arg: Any):
    return QueryExpression(
        (arg,),
        (QueryOperator('!'),)
    )


def test_query_expression_parser():

    expectations = {
        "!test": qne(qre('test')),
        "`safe`": QueryExpression(
            (
                TextExpression(
                    (
                        StringToken("safe"),
                    ),
                    ()
                ),
            ),
            ()
        ),
        "first & !(second ^ third) - 4 * 5 | sixth": QueryExpression(
            (
                qre('first'),
                quick_parse(QueryExpression, '!(second ^ third)'),
                quick_parse(ArithmeticExpression, '4 * 5'),
                qre('sixth'),
            ),
            (
                QueryOperator('&'),
                ArithmeticOperator('-'),
                QueryOperator('|'),
            )
        ),

        "first & !second ^ third - 4 * 5 | sixth" : QueryExpression(
            (
                qre('first'),
                qne(qre('second')),
                quick_parse(ArithmeticExpression, 'third - 4 * 5'),
                qre('sixth'),
            ),
            (
                QueryOperator('&'),
                QueryOperator('^'),
                QueryOperator('|'),
            )
        ),

        "!test & 3*7": QueryExpression(
            (
                qne(qre('test')),
                quick_parse(ArithmeticExpression, '3*7')
            ),
            (
                QueryOperator('&'),
            )
        ),
        "!test & ok": QueryExpression(
            (
                qne(qre('test')),
                qre('ok')
            ),
            (
                QueryOperator('&'),
            )
        ),

        "keep calm & !<kill> the messenger | be uninformed": QueryExpression(
            (
                qre('keep calm'),
                qne(
                    quick_parse(TriggerExpression, '<kill> the messenger')
                ),
                qre('be uninformed')
            ),
            (
                QueryOperator('&'),
                QueryOperator('|')
            )
        ),
        "* | !<trigger>": QueryExpression(
            (
                qre('void'),
                qne(quick_parse(TriggerExpression, '<trigger>'))
            ),
            (
                QueryOperator('|'),
            )
        ),
        "state & <trigger>": QueryExpression(
            (
                qre('state'),
                quick_parse(TriggerExpression, '<trigger>')
            ),
            (
                QueryOperator('&'),
            )
        ),
        "state & !<trigger>": QueryExpression(
            (
                qre('state'),
                qne(quick_parse(TriggerExpression, '<trigger>'))
            ),
            (
                QueryOperator('&'),
            )
        ),
        "4+3": QueryExpression(
            (
                quick_parse(ArithmeticExpression, '4+3'),
            ),
            (),
        ),
        "4+3 & test": QueryExpression(
            (
                quick_parse(ArithmeticExpression, '4+3'),
                qre('test'),
            ),
            (QueryOperator('&'),)
        ),
        "a & !b": QueryExpression(
            (
                qre('a'),
                QueryExpression(
                    (qre('b'),),
                    (QueryOperator('!'),)
                )
            ),
            (QueryOperator('&'),)
        ),
        "a & !(brett + 7 != 4) | d": QueryExpression(
            (
                qre('a'),
                qne(
                    QueryExpression(
                        (qdae('brett + 7'), qdae('4')),
                        (QueryOperator("!="),)
                    )
                ),
                qre('d'),
            ),
            (QueryOperator("&"), QueryOperator("|"))
        ),
        "A == 1": QueryExpression(
            (qre("A"), qdae("1")),
            (QueryOperator('=='),)
        ),
        "A & B != C | D": QueryExpression(
            (qre("A"), qre("B"), qre("C"), qre("D")),
            (QueryOperator('&'), QueryOperator('!='), QueryOperator('|'))
        ),
        'Hurt & <Turn Ended>': QueryExpression(
            (qre('Hurt'), quick_parse(TriggerExpression, '<Turn Ended>')),
            (QueryOperator('&'),)
        ),
    }

    results = collect_parsing_expectations(expectations, QueryExpressionParsers.expression)
    for result in results:
        result = result.as_strings()
        assert result.actual == result.expected,  result.parser_input
