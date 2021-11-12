from typing import Dict, Any

from parsita import Success, Failure, lit, reg

from Parser.Tokenizers.operator_tokenizers import MPLOperatorParsers, MPLOperator, StateOperator, StateOperatorParsers
from Tests import collect_parsing_expectations


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


def test_mploperator_parsers():
    expectations = {
        '->': MPLOperator('ANY', 'CONSUME', 'STATE', 0),
        '~@': MPLOperator('ANY', 'OBSERVE', 'ACTION', 0),
        '@~>': Failure,
        '|->': MPLOperator('FORK', 'CONSUME', 'STATE', 0),
        '|~@': MPLOperator('FORK', 'OBSERVE', 'ACTION', 0),
    }

    results = assert_parsing_expectations(expectations, MPLOperatorParsers.operator)


def test_mploperator_parsers_depth():
    expectations = {
        "1234      |-> 0123": MPLOperator('FORK', 'CONSUME', 'STATE', 10)
    }

    parser = reg(r"\d+") >> MPLOperatorParsers.operator << reg(r"\d+")
    results = collect_parsing_expectations(expectations, parser)

    for result in results:
        assert result.actual == result.expected


def test_stateoperator_parsers():
    expectations = {
        '&': StateOperator('&'),
        '|': StateOperator('|'),
    }

    results = assert_parsing_expectations(expectations, StateOperatorParsers.operator)