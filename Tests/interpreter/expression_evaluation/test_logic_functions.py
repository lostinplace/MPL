from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference, Ref
from mpl.interpreter.reference_resolution.reference_graph_resolution import MPLEntity, MPLEntityClass
from sympy import abc, N, symbols

from mpl.lib import fs
from mpl.lib.query_logic import query_and, query_negate, query_or, query_xor, eval_expr_with_context, query_gt, \
    query_lt, \
    query_ge, query_le, query_eq, query_neq, target_and, target_or, target_xor

red, black, uncolored = symbols('red black uncolored')
bank = Reference('bank').as_symbol()
cost = Reference('cost').as_symbol()


context = {
    Reference('a'): 5,
    Reference('b'): 'test',
    Reference('state one'):
        MPLEntity(0, 'state one', MPLEntityClass.MACHINE, fs(5, -8.0, 'test')),
    Reference('bank'): MPLEntity(1, 'bank', MPLEntityClass.VARIABLE, fs(3 * red + 5 * black)),
    Reference('cost'): 2 * red + 3 * uncolored,
    Reference('notactive'): MPLEntity(1, 'notactive', MPLEntityClass.VARIABLE, fs()),

}


def test_ref_symbol_relationship():

    example_context = {
        Ref('Random'): 1,
        Ref('with spaces test'): 2,
    }

    test_sym = Ref('Random').as_symbol()

    from sympy import Symbol
    assert isinstance(test_sym, Symbol)

    decoded = Reference.decode(Ref('Random'))
    result = example_context.get(decoded)
    assert result == 1



def test_ref_as_symbol_math():
    expected = Ref('a').as_symbol() + Ref('b').as_symbol()
    actual = Ref('a') + Ref('b')
    assert expected == actual
    expected = Ref('a').as_symbol() + 3 + Ref('b').as_symbol()
    actual = Ref('a') + 3 + Ref('b')
    assert expected == actual


def test_eval_expr_with_context():
    expectations = {
        Reference('state one') - 5: fs(N(-13.0), symbols('test') - 5),
        Ref('a') + Ref('b'): fs(symbols('test') + 5),
        Ref('a') + 1: fs(6),
        symbols('notactive'): fs(symbols('notactive')),
        Reference('notactive').as_symbol(): fs(),
        Reference('bank').as_symbol(): fs(context[Reference('bank')]),
        abc.d: fs(abc.d),
        Ref('a') + 3 + Ref('b'): fs(symbols('test') + 8),

        bank - cost: fs(red + 5 * black - 3 * uncolored),
        Ref('a')- 5: frozenset(),
    }


    for input, expected in expectations.items():

        actual = eval_expr_with_context(input, context)
        assert actual == expected, input


def test_logical_negate():

    expectations = {
        context[Ref('notactive')]: fs(1),
        symbols('bank'): fs(),
        fs(6): frozenset(),
        fs(abc.a + 3 + abc.b): frozenset(),
        frozenset(): fs(1),
    }

    for input, expected in expectations.items():
        actual = query_negate(input)
        assert actual == expected, input


def test_logical_and():

    expectations = {
        (fs(1), fs(2, 3)): fs(1, 2, 3),
        (fs(), fs(abc.a)): fs(),
        (fs(), fs()): fs(),
    }

    for input, expected in expectations.items():
        actual = query_and(*input)
        assert actual == expected, input


def test_logical_or():
    expectations = {
        (fs(abc.d), fs(6)): fs(abc.d, 6),
        (fs(abc.d), fs()): fs(abc.d),
        (fs(abc.d), fs(1,2,3)): fs(abc.d,1,2,3),
        (fs(), fs()): fs(),
    }

    for input, expected in expectations.items():
        actual = query_or(*input)
        assert actual == expected, input


def test_logical_xor():
    expectations = {
        (fs(abc.d), fs(6)): fs(),
        (fs(abc.d), fs()): fs(abc.d),
        (fs(abc.d), fs(1, 2, 3)): fs(),
        (fs(), fs()): fs(),
    }

    for input, expected in expectations.items():
        actual = query_xor(*input)
        assert actual == expected, input


def test_target_and():
    bank = MPLEntity(1, 'bank', MPLEntityClass.VARIABLE, fs(3 * Ref('red') + 5 * Ref('black')))
    cost_expr = 2 * Ref('red')
    cost = MPLEntity(1, 'cost', MPLEntityClass.VARIABLE, fs(cost_expr))

    expectations = {
        (fs(1), fs(2, 3)): fs(),
        (fs(bank), fs(abc.a)): fs(bank),
        (fs(bank), fs()): fs(bank),
        (fs(bank), fs(cost)): fs(bank, cost),
    }

    for input, expected in expectations.items():
        actual = target_and(*input)
        assert actual == expected, input


def test_target_or():
    bank = MPLEntity(1, 'bank', MPLEntityClass.VARIABLE, fs(3 * Ref('red') + 5 * Ref('black')))
    cost_expr = 2 * Ref('red')
    cost = MPLEntity(1, 'cost', MPLEntityClass.VARIABLE, fs(cost_expr))
    empty = MPLEntity(1, 'empty', MPLEntityClass.VARIABLE, fs())

    expectations = {
        (fs(1), fs(2, 3)): fs(),
        (fs(bank), fs(abc.a)): fs(bank),
        (fs(abc.a), fs(bank)): fs(bank),
        (fs(bank), fs()): fs(bank),
        (fs(bank), fs(empty)): fs(empty),
        (fs(empty), fs(bank)): fs(empty),
        (fs(bank), fs(cost)): fs(bank),
    }

    for input, expected in expectations.items():
        actual = target_or(*input)
        assert actual == expected, input


def test_target_xor():
    bank = MPLEntity(1, 'bank', MPLEntityClass.VARIABLE, fs(3 * Ref('red') + 5 * Ref('black')))
    cost_expr = 2 * Ref('red')
    cost = MPLEntity(1, 'cost', MPLEntityClass.VARIABLE, fs(cost_expr))
    empty = MPLEntity(1, 'empty', MPLEntityClass.VARIABLE, fs())
    empty_2 = MPLEntity(1, 'empty', MPLEntityClass.VARIABLE, fs())

    expectations = {
        (fs(1), fs(2, 3)): fs(),
        (fs(), fs(2, 3)): fs(),
        (fs(), fs()): fs(),
        (fs(bank), fs(abc.a)): fs(),
        (fs(bank), fs()): fs(bank),
        (fs(), fs(bank)): fs(bank),
        (fs(bank, cost), fs()): fs(bank, cost),
        (fs(), fs(bank, cost)): fs(bank, cost),
        (fs(bank), fs(empty)): fs(bank),
        (fs(empty), fs(bank)): fs(bank),
        (fs(empty), fs()): fs(empty),
        (fs(empty_2), fs(empty)): fs(empty_2),
        (fs(bank), fs(cost)): fs(),
        (fs(bank, cost), fs(empty_2)): fs(bank, cost),
        (fs(), fs(empty_2, empty)): fs(empty_2, empty),
    }

    for index, input in enumerate(expectations):
        expected = expectations[input]
        actual = target_xor(*input)
        assert actual == expected, index


def test_logical_gt():

    bank = MPLEntity(1, 'bank', MPLEntityClass.VARIABLE, fs(3 * Ref('red') + 5 * Ref('black')))
    cost_expr = 2 * Ref('red')
    cost = MPLEntity(1, 'cost', MPLEntityClass.VARIABLE, fs(cost_expr))

    expectations = {
        (fs(abc.d), fs()): fs(abc.d),
        (fs(bank, -12, 20), fs(N(6), cost)): fs(),
        (fs(bank, -12, 20), fs(6, cost)): fs(),
        (fs(bank, -12, 20), fs(6, cost, 20)): fs(),
        (fs(bank, 32, 20), fs(6, cost)): fs(bank, 32,20),
        (fs(bank,  20), fs(6)): fs(bank,  20),
        (fs(6), fs(12)): fs(),
        (fs(abc.d), fs(6)): fs(abc.d > 6),
        (fs(12), fs(6)): fs(12),
        (fs(N(12)), fs(6)): fs(N(12)),

    }

    for input, expected in expectations.items():
        actual = query_gt(input[0], input[1])
        assert actual == expected, input


def test_logical_eq():
    cost_expr = 3 * Ref('red') + 5 * Ref('black')
    bank = MPLEntity(1, 'bank', MPLEntityClass.VARIABLE, fs(cost_expr))
    cost = MPLEntity(1, 'cost', MPLEntityClass.VARIABLE, fs(cost_expr))

    expectations = {
        (fs(bank), fs(cost)): fs(bank, cost),
        (fs(12, bank), fs(N(12), bank)): fs(12, bank, N(12)),
        (fs(12, 20), fs(12, 20)): fs(12, 20),
        (fs(12, 20), fs(12, 20,6)): fs(),
        (fs(12, 20, 6), fs(12, 20)): fs(),
        (fs(12), fs(N(12))): fs(12, N(12)),
    }

    for input, expected in expectations.items():
        actual = query_eq(input[0], input[1])
        assert actual == expected, repr(input)


def test_logical_neq():
    cost_expr = 3 * Ref('red') + 5 * Ref('black')
    bank = MPLEntity(1, 'bank', MPLEntityClass.VARIABLE, fs(cost_expr))
    cost = MPLEntity(1, 'cost', MPLEntityClass.VARIABLE, fs(cost_expr))

    expectations = {
        (fs(12, 20), fs(12, 20, 6)): fs(6),
        (fs(bank), fs(cost)): fs(),
        (fs(12, bank), fs(N(12), bank)): fs(),
        (fs(12, 20), fs(12, 20)): fs(),
        (fs(12, 20, 6), fs(12, 20)): fs(6),
        (fs(12), fs(N(12))): fs(),
    }

    for input, expected in expectations.items():
        actual = query_neq(input[0], input[1])
        assert actual == expected, repr(input)


def test_logical_inequality_comparisons():

    bank = MPLEntity(1, 'bank', MPLEntityClass.VARIABLE, fs(3 * Ref('red') + 5 * Ref('black')))
    cost_expr = 2 * Ref('red')
    cost = MPLEntity(1, 'cost', MPLEntityClass.VARIABLE, fs(cost_expr))

    expectations = {
        (fs(), fs(abc.d)): {
            query_gt: fs(),
            query_lt: fs(1),
            query_ge: fs(),
            query_le: fs(1),
        },
        (fs(bank, -12, 20), fs(26, cost, 20)): {
            query_gt: fs(),
            query_lt: fs(),
            query_ge: fs(),
            query_le: fs(bank, -12, 20),
        },
        (fs(bank, -12, 20), fs(N(6), cost)): {
            query_gt: fs(),
            query_lt: fs(),
            query_ge: fs(),
            query_le: fs(),
        },
        (fs(bank, -12, 20), fs(6, cost)): {
            query_gt: fs(),
            query_lt: fs(),
            query_ge: fs(),
            query_le: fs(),
        },
        (fs(bank, 32, 20), fs(6, cost)): {
            query_gt: fs(bank, 32, 20),
            query_lt: fs(),
            query_ge: fs(bank, 32, 20),
            query_le: fs(),
        },
        (fs(bank,  20), fs(6)): {
            query_gt: fs(bank, 20),
            query_lt: fs(),
            query_ge: fs(bank, 20),
            query_le: fs(),
        },
        (fs(bank, 20), fs(20)): {
            query_gt: fs(),
            query_lt: fs(),
            query_ge: fs(bank, 20),
            query_le: fs(bank, 20),
        },
        (fs(6), fs(12)): {
            query_gt: fs(),
            query_lt: fs(6),
            query_ge: fs(),
            query_le: fs(6),
        },
        (fs(12), fs(12)): {
            query_gt: fs(),
            query_lt: fs(),
            query_ge: fs(12),
            query_le: fs(12),
        },
        (fs(abc.d), fs(6)): {
            query_gt: fs(abc.d > 6),
            query_lt: fs(abc.d < 6),
            query_ge: fs(abc.d >= 6),
            query_le: fs(abc.d <= 6),
        },
        (fs(abc.d), fs()): {
            query_gt: fs(abc.d),
            query_lt: fs(),
            query_ge: fs(abc.d),
            query_le: fs(),
        },
        (fs(12), fs(6)): {
            query_gt: fs(12),
            query_lt: fs(),
            query_ge: fs(12),
            query_le: fs(),
        },
        (fs(N(12)), fs(6)): {
            query_gt: fs(N(12)),
            query_lt: fs(),
            query_ge: fs(N(12)),
            query_le: fs(),
        },

    }

    for input, expected in expectations.items():
        for op, expected_op in expected.items():
            actual = op(input[0], input[1])
            assert actual == expected_op, f'{repr(op)}, {repr(input)}'
