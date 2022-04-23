from typing import Tuple, Optional

from sympy.core.relational import Relational, StrictLessThan, GreaterThan, LessThan

from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference, Ref

from sympy import abc, N, symbols, Symbol, StrictGreaterThan, Eq, solve_univariate_inequality, solve, Expr

from mpl.interpreter.expression_evaluation.engine_context import EngineContext

from mpl.interpreter.expression_evaluation.entity_value import EntityValue, ev_fv
from mpl.lib.query_logic.expression_processing import entity_value_from_expression
from mpl.lib.query_logic.query_operations import query_negate, query_and, query_or, query_xor
from mpl.lib.query_logic.target_operations import target_and, target_xor, target_or

red, black, uncolored = symbols('red black uncolored')
bank = Reference('bank').symbol
cost = Reference('cost').symbol


context_data = {
    Reference('a'): ev_fv(5),
    Reference('b'): ev_fv('test'),
    Reference('state one'): ev_fv(5, -8.0, 'test'),
    Reference('bank'): ev_fv(3 * red + 5 * black),
    Reference('cost'): 2 * red + 3 * uncolored,
    Reference('notactive'): ev_fv(),
    Ref('red', ev_fv('symbol')): ev_fv(),
    Ref('black', ev_fv('symbol')): ev_fv(),
    Ref('uncolored', ev_fv('symbol')): ev_fv(),
}


def test_ref_symbol_relationship():

    example_context = {
        Ref('Random'): 1,
        Ref('with spaces test'): 2,
    }

    test_sym = Ref('Random').symbol

    from sympy import Symbol
    assert isinstance(test_sym, Symbol)

    decoded = Reference.decode(Ref('Random').symbol)
    result = example_context.get(decoded)
    assert result == 1


def test_ref_as_symbol_math():
    expected = Ref('a').symbol + Ref('b').symbol
    actual = Ref('a') + Ref('b')
    assert expected == actual
    expected = Ref('a').symbol + 3 + Ref('b').symbol
    actual = Ref('a') + 3 + Ref('b')
    assert expected == actual


def test_eval_expr_with_context():
    context = EngineContext.from_dict(context_data)

    expectations = {
        Reference('bank').symbol: context[Reference('bank')] | Ref('bank'),
        Reference('state one') - 5: ev_fv(N(-13.0), Symbol('`test`') - 5),
        Ref('a') + Ref('b'): ev_fv(Symbol('`test`') + 5),
        Ref('a') + 1: ev_fv(6),
        Reference('notactive').symbol: ev_fv(Ref('notactive')),
        abc.d: ev_fv(Ref('d')),
        Ref('a') + 3 + Ref('b'): ev_fv(Symbol('`test`') + 8),

        bank - cost: ev_fv(red + 5 * black - 3 * uncolored),
        Ref('a') - 5: ev_fv(),
    }

    for value, expected in expectations.items():

        actual = entity_value_from_expression(value, context)
        assert actual == expected, value


def test_logical_negate():
    context = EngineContext.from_dict(context_data)

    expectations = {
        context[Ref('notactive')]: ev_fv(1),
        symbols('bank'): ev_fv(),
        ev_fv(6): ev_fv(),
        ev_fv(abc.a + 3 + abc.b): ev_fv(),
        ev_fv(): ev_fv(1),
    }

    for value, expected in expectations.items():
        actual = query_negate(value)
        assert actual == expected, value


def test_logical_and():

    expectations = {
        (ev_fv(1), ev_fv(2, 3)): ev_fv(1, 2, 3),
        (ev_fv(), ev_fv(abc.a)): ev_fv(),
        (ev_fv(), ev_fv()): ev_fv(),
    }

    for value, expected in expectations.items():
        actual = query_and(*value)
        assert actual == expected, value


def test_logical_or():
    expectations = {
        (ev_fv(abc.d), ev_fv(6)): ev_fv(abc.d, 6),
        (ev_fv(abc.d), ev_fv()): ev_fv(abc.d),
        (ev_fv(abc.d), ev_fv(1, 2, 3)): ev_fv(abc.d, 1, 2, 3),
        (ev_fv(), ev_fv()): ev_fv(),
    }

    for value, expected in expectations.items():
        actual = query_or(*value)
        assert actual == expected, value


def test_logical_xor():
    expectations = {
        (ev_fv(abc.d), ev_fv(6)): ev_fv(),
        (ev_fv(abc.d), ev_fv()): ev_fv(abc.d),
        (ev_fv(abc.d), ev_fv(1, 2, 3)): ev_fv(),
        (ev_fv(), ev_fv()): ev_fv(),
    }

    for value, expected in expectations.items():
        actual = query_xor(*value)
        assert actual == expected, value


def test_target_and():
    bank = ev_fv(3 * Ref('red') + 5 * Ref('black'))
    cost_expr = 2 * Ref('red')
    cost = ev_fv(cost_expr)

    expectations = {
        (ev_fv(1), ev_fv(2, 3)): ev_fv(1, 2, 3),
        (ev_fv(bank), ev_fv(abc.a)): bank | abc.a,
        (ev_fv(bank), ev_fv()): bank,
        (ev_fv(bank), ev_fv(cost)): bank | cost,
    }

    for value, expected in expectations.items():
        actual = target_and(*value)
        assert actual == expected, value


def test_target_or():
    bank = ev_fv(3 * Ref('red') + 5 * Ref('black'))
    cost_expr = 2 * Ref('red')
    cost = ev_fv(cost_expr)
    empty = ev_fv()

    expectations = {
        (ev_fv(1), ev_fv(2, 3)): ev_fv(1, 2, 3),
        (bank, ev_fv(abc.a)): bank | abc.a,
        (ev_fv(abc.a), bank): bank | abc.a,
        (bank, ev_fv()): bank,
        (bank, ev_fv(Ref('cost'))): bank,
        (bank, empty): bank,
        (empty, bank): bank,
        (bank, cost): bank | cost,
    }

    for value, expected in expectations.items():
        actual = target_or(*value)
        equals_0 = actual == value[0]
        equals_1 = actual == value[1]
        assert equals_0 or equals_1, value


def test_target_xor():
    bank = ev_fv(3 * Ref('red') + 5 * Ref('black'))
    cost_expr = 2 * Ref('red')
    cost = ev_fv(cost_expr)
    empty = ev_fv()
    empty_2 = ev_fv()

    expectations = {
        (ev_fv(1), ev_fv(2, 3)): ev_fv(),
        (ev_fv(), ev_fv(2, 3)): ev_fv(2, 3),
        (ev_fv(), ev_fv()): ev_fv(),
        (bank, ev_fv(abc.a)): ev_fv(),
        (bank, ev_fv()): bank,
        (ev_fv(), bank): bank,
        (bank | cost, ev_fv()): bank | cost,
        (ev_fv(), bank | cost): bank | cost,
        (bank, empty): bank,
        (empty, bank): bank,
        (empty, ev_fv()): empty,
        (empty_2, empty): empty_2,
        (bank, ev_fv(cost)): ev_fv(),
        (bank | cost, empty_2): bank | cost,
        (ev_fv(), empty_2 | empty): empty_2 | empty,
    }

    for index, value in enumerate(expectations):
        expected = expectations[value]
        actual = target_xor(*value)
        assert actual == expected, index


def test_logical_gt():

    bank = ev_fv(3 * Ref('red') + 5 * Ref('black'))
    cost_expr = 2 * Ref('red')
    cost = ev_fv(cost_expr)

    expectations = {
        (
            ev_fv(red > 3, red < 7),
            ev_fv(red > 9)
        ): ev_fv(),
        (
            ev_fv(red, red > 3, black < 5),
            ev_fv(1, red > 12, black < -2)
        ): ev_fv(red, red > 12, black < -2),
        (
            ev_fv(Ref('b'), red, 12),
            ev_fv(14)
        ): ev_fv(Ref('b'), red, red > 14, 12).with_p(1/2),
        (
            ev_fv(12),
            ev_fv(6)
        ): ev_fv(12),
        (
            ev_fv(N(12)),
            ev_fv(6)
        ): ev_fv(N(12)),
        (
            ev_fv(-12, 20) | bank,
            ev_fv(N(6)) | cost
        ):
            ev_fv({-12, -6 > red, 20, 5*black + 3*red, black > -red/5, black > 1.2 - 0.6*red}).with_p(5/6),
        (
            ev_fv(abc.d),
            ev_fv()
        ): ev_fv(abc.d),
        (
            bank - cost,
            bank
        ): EntityValue(value=frozenset({0 > red, 5*black + red}), p=1.0),
        (
            ev_fv(32, 20) | bank,
            ev_fv(6) | cost
        ): ev_fv(32, 20) | bank,
        (
            bank | 20,
            ev_fv(6)
        ): bank | 20,
        (
            ev_fv(6),
            ev_fv(12)
        ): ev_fv(),
        (
            ev_fv(abc.d),
            ev_fv(6)
        ): ev_fv(abc.d > 6, abc.d),

    }

    for (x, y), expected in expectations.items():
        actual = x > y
        assert actual == expected, f'{x} > {y}'


def test_logical_eq():
    cost_expr = 3 * Ref('red') + 5 * Ref('black')
    bank = cost_expr
    cost = cost_expr

    expectations = {
        (
            ev_fv(15, Ref('ok'), red, black > 13),
            ev_fv(N(15), Ref('not ok'), 19, black > 17)
        ): ev_fv(15, N(15), Ref('ok'), Ref('not ok'), Eq(red, 19), black > 17),
        (
            ev_fv(15, Ref('ok'), red),
            ev_fv(N(15), Ref('ok'), 19, black > 17)
        ): ev_fv(15, N(15), Ref('ok'), Eq(red, 19), black > 17),
        (
            ev_fv(15, Ref('ok'), red),
            ev_fv(N(15), Ref('ok'), 19)
        ): ev_fv(15, N(15), Ref('ok'), Eq(red, 19)),
        (
            ev_fv(15, Ref('ok'), red > 3),
            ev_fv(N(15), Ref('ok'), red > 5)
        ): ev_fv(15, N(15), Ref('ok'), red > 5),
        (
            ev_fv(3, 'test', Ref('ok'), red-3),
            ev_fv(3, 'test', Ref('ok'), black + 2)
        ): ev_fv(3, 'test', Ref('ok'), Eq(red - 3, black + 2)),
        (
            ev_fv(bank), ev_fv(cost)
        ): ev_fv(bank, cost),
        (
            ev_fv(12, bank),
            ev_fv(N(12), bank)
        ): ev_fv(12, N(12), bank),
        (
            ev_fv(12, 20),
            ev_fv(12, 20)
        ): ev_fv(12, 20),
        (
            ev_fv(12, 20),
            ev_fv(12, 20, 6)
        ): ev_fv(),
        (
            ev_fv(12, 20, 6),
            ev_fv(12, 20)
        ): ev_fv(),
        (
            ev_fv(12),
            ev_fv(N(12))
        ): ev_fv(12, N(12)),
    }

    for (o, B), expectation in expectations.items():
        actual = o == B
        assert actual == expectation


def test_logical_inequality_comparisons():

    bank = ev_fv(3 * Ref('red') + 5 * Ref('black'))
    cost_expr = 2 * Ref('red')
    cost = ev_fv(cost_expr)

    e_1 = ev_fv(1, -1, Ref('lowest'), red)
    e_2 = ev_fv(2, 3, Ref('higher than lowest'), black)
    e_3 = ev_fv(3, 4)
    e_4 = ev_fv(5, 6)

    tmp = e_1 > ev_fv()
    assert tmp == e_1
    tmp = e_2 > e_1
    assert tmp == ev_fv(2, 3, Ref('higher than lowest'), black > 1, black > red, 2 > red, black)
    tmp = e_1 > e_2
    assert tmp == ev_fv(-1, 1, Ref('lowest'), black < -1, black < red, red, red > 3).with_p(2/3)
    tmp = e_1 < e_2
    assert tmp == ev_fv(-1, 1, Ref('lowest'), black > 1, black > red, red, red < 2)
    tmp = e_3 > e_4
    assert tmp == ev_fv()
    tmp = e_3 < e_4
    assert tmp == e_3
    tmp = e_4 > e_3
    assert tmp == e_4
    tmp = bank - cost > ev_fv(0)
    assert tmp
    bankrupt = ev_fv(bank) - ev_fv(12*red + 20* black)
    tmp = bankrupt > ev_fv(red >= 1, black >= 1)
    # TODO: this is not correct, need to implement multivarriate inequality solver from here:
    # https://www.dcsc.tudelft.nl/~bdeschutter/pub/rep/93_71.pdf
    # assert not tmp
