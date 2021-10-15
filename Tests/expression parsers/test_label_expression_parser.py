from typing import Dict, Any

from parsita import Success, Failure

from Parser.ExpressionParsers.label_expression_parser import LabelExpressionParsers, LabelExpression
from Parser.Tokenizers.simple_value_tokenizer import ReservedToken, LabelToken


def assert_parsing_expectations(expectations: Dict[str, Any], parser):
    results = []
    for (v, expected_outcome) in expectations.items():
        result = parser.parse(v)

        if expected_outcome is Failure:
            assert type(result) is Failure
            continue
        assert type(result) == Success
        assert result == Success(expected_outcome)
        results.append((v, expected_outcome, result))
    return results


def test_label_expression_parsers():
    expectations = {
        "a:TEST": LabelExpression(
            'a', 0, LabelToken('a'),
            LabelExpression("TEST", 2, ReservedToken("TEST"), None)
        ),
        "Wumpus: MACHINE": LabelExpression('Wumpus', 0, LabelToken('Wumpus'),
                                           LabelExpression("MACHINE", 8, ReservedToken("MACHINE"), None)),
        "Ok: Health": LabelExpression('Ok', 0, LabelToken('Ok'),
                                      LabelExpression("Health", 4, LabelToken("Health"), None)),
        'help: Me': LabelExpression('help', 0, LabelToken('help'),
                                      LabelExpression("Me", 6, LabelToken("Me"), None)),
        "Ok: Health : Body State": LabelExpression(
            'Ok', 0, LabelToken('Ok'),
            LabelExpression(
               "Health", 4, LabelToken("Health"),
               LabelExpression(
                   "Body State",
                   13,
                   LabelToken("Body State"),
                   None
               ),
            ),
        ),
    }

    assert_parsing_expectations(expectations, LabelExpressionParsers.expression)

