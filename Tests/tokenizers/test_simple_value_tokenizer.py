from typing import Dict, Any

from parsita import Success, Failure

from Parser.Tokenizers.simple_value_tokenizer import SimpleValueTokenizers, NumberToken, StringToken, ReferenceToken
from Tests import collect_parsing_expectations


def assert_parsing_expectations(expectations: Dict[str, Any], parser):
    results = []
    for (v, expected_outcome) in expectations.items():
        expected_value = v
        result = parser.parse(v)

        if isinstance(expected_outcome, tuple):
            expected_outcome, expected_value = expected_outcome

        if expected_outcome is Failure:
            assert type(result) is Failure
            continue
        assert type(result) == Success
        assert result == Success(expected_outcome(expected_value))
        results.append((v, expected_outcome, result))
    return results


def test_simple_value_tokenization():
    expectations = {
        "t`dsf`": Failure,
        "a": ReferenceToken('a'),
        "Test Mee": ReferenceToken("Test Mee"),
        "Im a simple reference": ReferenceToken("Im a simple reference"),
        "Im a broken 12 reference": ReferenceToken("Im a broken 12 reference"),
        "a + b": Failure,
        "-10.556ds": Failure,
        "21313.2121": NumberToken("21313.2121"),
        "0.2121": NumberToken("0.2121"),
        "-10": NumberToken("-10"),
        "-10.556": NumberToken("-10.556"),
        "12e-5": NumberToken("12e-5"),
        "123": NumberToken("123"),
        "MACHINE": ReferenceToken("MACHINE"),
        "`Testing`": StringToken("Testing"),
        "`ldksjj dljsj fjslkdj`": StringToken("ldksjj dljsj fjslkdj"),

    }

    results = collect_parsing_expectations(expectations, SimpleValueTokenizers.token)
    for result in results:
        result = result.as_strings()
        assert result.actual == result.expected
