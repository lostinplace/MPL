from typing import Dict, Any

from parsita import Success, Failure

from Parser.Tokenizers.simple_value_tokenizer import SimpleValueTokenizers, NumberToken, ReservedToken, StringToken, LabelToken


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
        "a": LabelToken,
        "t`dsf`": Failure,
        "Test Mee": LabelToken,
        "Im a simple label": LabelToken,
        "Im a broken 12 label": Failure,
        "a + b": Failure,
        "-10.556ds": Failure,
        "21313.2121": NumberToken,
        "0.2121": NumberToken,
        "-10": NumberToken,
        "-10.556": NumberToken,
        "12e-5": NumberToken,
        "123": NumberToken,
        "MACHINE": ReservedToken,
        "STATE": ReservedToken,
        "TRIGGER": ReservedToken,
        "INT": ReservedToken,
        "DOUBLE": ReservedToken,
        "STRING": ReservedToken,
        "SET": ReservedToken,
        "DICT": ReservedToken,
        "BOOL": ReservedToken,
        "NO-CACHE": ReservedToken,
        "MACHINE": ReservedToken,
        "FUNC": ReservedToken,
        "`Testing`": (StringToken, "Testing"),
        "`ldksjj dljsj fjslkdj`": (StringToken, "ldksjj dljsj fjslkdj")

    }

    results = assert_parsing_expectations(expectations, SimpleValueTokenizers.token)