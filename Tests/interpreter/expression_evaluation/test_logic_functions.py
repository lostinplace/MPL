from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference, Ref

from sympy import abc, N, symbols, Symbol

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
    ev_fv(2 * red < -12, 2 * red < 20, 5 * black + 3 * red > 2 * red, 5 * black + 3 * red > 6.0)

    expectations = {
        (ev_fv(abc.d), ev_fv()): ev_fv(abc.d),
        (ev_fv(-12, 20) | bank, ev_fv(N(6)) | cost):
            ev_fv({5*black + 3*red > 6.0, red < -6, red < 10, red > -5*black}),
        (bank - cost, bank): ev_fv({red < 0}),
        (ev_fv(32, 20) | bank, ev_fv(6) | cost): ev_fv(32, 20) | bank,
        (bank | 20, ev_fv(6)): bank | 20,
        (ev_fv(6), ev_fv(12)): ev_fv(),
        (ev_fv(abc.d), ev_fv(6)): ev_fv(abc.d > 6),
        (ev_fv(12), ev_fv(6)): ev_fv(12),
        (ev_fv(N(12)), ev_fv(6)): ev_fv(N(12)),

    }

    for value, expected in expectations.items():
        x = ev_fv(value[0])
        y = ev_fv(value[1])
        actual = x > y
        assert actual == expected, value


def test_logical_eq():
    cost_expr = 3 * Ref('red') + 5 * Ref('black')
    bank = EntityValue(ev_fv(cost_expr))
    cost = EntityValue(ev_fv(cost_expr))

    expectations = {
        (bank, ev_fv(cost)): ev_fv(bank, cost),
        (ev_fv(12, bank), ev_fv(N(12), bank)): ev_fv(12, bank, N(12)),
        (ev_fv(12, 20), ev_fv(12, 20)): ev_fv(12, 20),
        (ev_fv(12, 20), ev_fv(12, 20,6)): ev_fv(),
        (ev_fv(12, 20, 6), ev_fv(12, 20)): ev_fv(),
        (ev_fv(12), ev_fv(N(12))): ev_fv(12, N(12)),
    }

    for value, expected in expectations.items():
        x = ev_fv(value[0])
        y = ev_fv(value[1])
        actual = x == y
        assert actual == expected, value


def test_logical_inequality_comparisons():

    bank = EntityValue(ev_fv(3 * Ref('red') + 5 * Ref('black')))
    cost_expr = 2 * Ref('red')
    cost = EntityValue(ev_fv(cost_expr))

    expectations = {
        (ev_fv(), ev_fv(abc.d)): {
            EntityValue.__gt__: ev_fv(),
            EntityValue.__lt__: ev_fv(1),
            EntityValue.__ge__: ev_fv(),
            EntityValue.__le__: ev_fv(1),
        },
        (ev_fv(bank, -12, 20), ev_fv(26, cost, 20)): {
            EntityValue.__gt__: ev_fv(),
            EntityValue.__lt__: ev_fv(),
            EntityValue.__ge__: ev_fv(),
            EntityValue.__le__: ev_fv(bank, -12, 20),
        },
        (ev_fv(bank, -12, 20), ev_fv(N(6), cost)): {
            EntityValue.__gt__: ev_fv(),
            EntityValue.__lt__: ev_fv(),
            EntityValue.__ge__: ev_fv(),
            EntityValue.__le__: ev_fv(),
        },
        (ev_fv(bank, -12, 20), ev_fv(6, cost)): {
            EntityValue.__gt__: ev_fv(),
            EntityValue.__lt__: ev_fv(),
            EntityValue.__ge__: ev_fv(),
            EntityValue.__le__: ev_fv(),
        },
        (ev_fv(bank, 32, 20), ev_fv(6, cost)): {
            EntityValue.__gt__: ev_fv(bank, 32, 20),
            EntityValue.__lt__: ev_fv(),
            EntityValue.__ge__: ev_fv(bank, 32, 20),
            EntityValue.__le__: ev_fv(),
        },
        (ev_fv(bank,  20), ev_fv(6)): {
            EntityValue.__gt__: ev_fv(bank, 20),
            EntityValue.__lt__: ev_fv(),
            EntityValue.__ge__: ev_fv(bank, 20),
            EntityValue.__le__: ev_fv(),
        },
        (ev_fv(bank, 20), ev_fv(20)): {
            EntityValue.__gt__: ev_fv(),
            EntityValue.__lt__: ev_fv(),
            EntityValue.__ge__: ev_fv(bank, 20),
            EntityValue.__le__: ev_fv(bank, 20),
        },
        (ev_fv(6), ev_fv(12)): {
            EntityValue.__gt__: ev_fv(),
            EntityValue.__lt__: ev_fv(6),
            EntityValue.__ge__: ev_fv(),
            EntityValue.__le__: ev_fv(6),
        },
        (ev_fv(12), ev_fv(12)): {
            EntityValue.__gt__: ev_fv(),
            EntityValue.__lt__: ev_fv(),
            EntityValue.__ge__: ev_fv(12),
            EntityValue.__le__: ev_fv(12),
        },
        (ev_fv(abc.d), ev_fv(6)): {
            EntityValue.__gt__: ev_fv(abc.d > 6),
            EntityValue.__lt__: ev_fv(abc.d < 6),
            EntityValue.__ge__: ev_fv(abc.d >= 6),
            EntityValue.__le__: ev_fv(abc.d <= 6),
        },
        (ev_fv(abc.d), ev_fv()): {
            EntityValue.__gt__: ev_fv(abc.d),
            EntityValue.__lt__: ev_fv(),
            EntityValue.__ge__: ev_fv(abc.d),
            EntityValue.__le__: ev_fv(),
        },
        (ev_fv(12), ev_fv(6)): {
            EntityValue.__gt__: ev_fv(12),
            EntityValue.__lt__: ev_fv(),
            EntityValue.__ge__: ev_fv(12),
            EntityValue.__le__: ev_fv(),
        },
        (ev_fv(N(12)), ev_fv(6)): {
            EntityValue.__gt__: ev_fv(N(12)),
            EntityValue.__lt__: ev_fv(),
            EntityValue.__ge__: ev_fv(N(12)),
            EntityValue.__le__: ev_fv(),
        },

    }

    for value, expected in expectations.items():
        for op, expected_op in expected.items():
            x = ev_fv(value[0])
            y = ev_fv(value[1])
            actual = op(x, y)
            assert actual == expected_op, value
