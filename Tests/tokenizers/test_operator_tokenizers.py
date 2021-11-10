from typing import Dict, Any

from parsita import Success, Failure, lit

from Parser.Tokenizers.operator_tokenizers import MPLOperatorParsers, MPLOperator, StateOperator, StateOperatorParsers


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
        '*-*': MPLOperator('EVENT', 'CONSUME', 'EVENT', 0),
        '*~@': MPLOperator('EVENT', 'OBSERVE', 'ACTION', 0),
        '@~>': Failure,
        '|->': MPLOperator('FORK', 'CONSUME', 'STATE', 0),
        '|~@': MPLOperator('FORK', 'OBSERVE', 'ACTION', 0),
        '   |~@': MPLOperator('FORK', 'OBSERVE', 'ACTION', 3),
    }

    results = assert_parsing_expectations(expectations, MPLOperatorParsers.operator)


def test_mploperator_parsers_depth():
    expectation = "1234 |-> 0123"
    test_parser = lit('1234') >> MPLOperatorParsers.operator << '0123'
    result = test_parser.parse(expectation)
    assert result == Success(MPLOperator('FORK', 'CONSUME', 'STATE', 5))


def test_stateoperator_parsers():
    expectations = {
        '&': StateOperator('&'),
        '|': StateOperator('|'),
    }

    results = assert_parsing_expectations(expectations, StateOperatorParsers.operator)