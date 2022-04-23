import pytest

from mpl.lib import fs
from mpl.lib.relational_math import red, ineq_resolver, simplify_relational_set, black


def test_reduction_of_multiple_univariate_inequalities():
    expectations = {
        fs(red < 13, red < 9, red < 7, red > 3, red > -2): fs(red < 7, red > 3),
        fs(red < 5, red > 2): fs(red < 5, red > 2),
        fs(red > 3, red < 1): False,
        fs(red > 3, red > 1): fs(3 < red),
        fs(red > 3, red > 1, red < -2): False,
    }

    for ineq, expected in expectations.items():
        actual = ineq_resolver(ineq, red)
        if actual is False:
            assert expected is False
        else:
            assert str(sorted(actual, key=str)) == str(sorted(expected, key=str))


def test_complicated_reduction_of_multiple_enqualities():
    expectations = {
        fs(-3 * red < 3 * red + 18, red > -12, 2 * red < -3 * red): frozenset({red < 0, red > -3}),
    }

    for ineq, expected in expectations.items():
        actual = simplify_relational_set(ineq)
        assert actual == expected


@pytest.mark.skip(reason="TODO: fix this test")
def test_simple_reduction_of_bivariate_inequalities():
    # TODO:  This needs a bunch of work, see https://www.dcsc.tudelft.nl/~bdeschutter/pub/rep/93_71.pdf
    red_val = 3
    black_val = 7

    expectations = {
        fs(
            5 * red > 2 * black,
            red < black,
            red < black + 2,
            1.5 * red < black - 1,
        ): fs(red < black - 1),
    }

    for ineq, expected in expectations.items():
        actual = simplify_relational_set(ineq)
        assert actual == expected
