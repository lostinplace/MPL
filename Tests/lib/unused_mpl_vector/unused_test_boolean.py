from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference
from mpl.lib.mpl_vector import Factor, fs, BOR, eval_boolean_factor, eval_boolean_factor_set, eval_boolean_term, \
    MPLVector, MPLAlgebra, eval_boolean_vector

a = Reference('a')
b = Reference('b')
c = Reference('c')
d = Reference('d')
e = Reference('e')
cache = {
    a: 1,
    b: 0,
    c: '',
    d: 'test',
    e: 100,
}


def unused_test_eval_factor_for_boolean_algebra():

    expectations = {
        Factor(1, Factor(1, Reference('missing'))): Factor(1, Factor(1, Reference('missing'))),
        Factor(a, Reference('missing')): Factor(1, Reference('missing')),
        Factor(1, 1): BOR(fs(1)),
        Factor(0, 0): BOR(fs(1)),
        Factor(1, 0.0): BOR(fs(1)),
        Factor(0, 1): BOR.from_args({}, 1),
        Factor(1, 0): BOR.from_args({}, 1),
        Factor(1, Factor(1, 0)): BOR.from_args({}, 1),
        Factor(1, Factor(1, 1)): BOR(fs(1)),
        Factor(a, c): BOR.from_args({}, 1),
        Factor(a, d): BOR(fs(1, 'test')),
        Factor(e, d): BOR(fs(100, 'test')),
        Factor(a, Factor(d, e)): BOR(fs(1, 'test', 100)),

    }
    for input in expectations:
        expected = expectations[input]
        actual = eval_boolean_factor(input, cache)
        assert actual == expected, input


def unused_test_eval_boolean_factor_set():
    expectations = {
        fs(
            Factor(a, d),
            Factor(e, a),
            Factor(b, 'tricky')
        ): BOR.from_args({}, {1, 100, 'test', 'tricky'}),
        fs(
            Factor(a, d),
            Factor(e, a),
            Factor('ok', c)
        ): BOR.from_args({}, {1, 100, 'test', 'ok'}),
        fs(
            Factor(1, 1),
            Factor(2, 1),
            Factor(3, 0)
        ): BOR.from_args({}, {1, 2, 3}),
        fs(
            Factor(1, 1),
            Factor(1, 0),
        ): BOR.from_args({}, {1}),
        fs(
            Factor(1, 1),
            Factor(1, 1),
        ): BOR.from_args({1}, {}),
        fs(
            Factor(1, 2),
            Factor(3, 4),
        ): BOR.from_args({1, 2, 3, 4}, {}),

        fs(
            Factor(1, 1),
            Factor(2, 1),
            Factor(0, 0)
        ): BOR.from_args({1, 2}, {}),
    }

    for input in expectations:
        expected = expectations[input]
        actual = eval_boolean_factor_set(input, cache)
        assert actual == expected, input


def unused_test_eval_boolean_term():
    fs_1 = fs(
            Factor(a, d),
            Factor(e, a),
            Factor(b, 'tricky')
        )
    fs_1_product = BOR.from_args({}, {1, 100, 'test', 'tricky'})

    expectations = {
        (fs_1, -1): ~fs_1_product,
        (fs_1, 1): fs_1_product,
        (fs_1, 0): BOR.from_args({}),
    }

    for input in expectations:
        expected = expectations[input]
        actual = eval_boolean_term(input, cache)
        assert actual == expected, input


def unused_test_BOR_or():
    fs_1_product = BOR.from_args({}, {1, 100, 'test', 'tricky'})
    fs_2_product = BOR.from_args({}, {1, 100, 'test', 'ok'})

    expectations = {
        (~fs_1_product, fs_2_product): BOR.from_args({1, 100, 'test', 'tricky'}, {1, 100, 'test', 'ok'})
    }

    for input in expectations:
        expected = expectations[input]
        actual = input[0] | input[1]
        assert actual == expected, input


def unused_test_eval_boolean_vector():
    fs_1 = fs(
        Factor(a, d),
        Factor(e, a),
        Factor(b, 'tricky')
    )
    fs_1_product = BOR.from_args({}, {1, 100, 'test', 'tricky'})

    fs_2 = fs(
        Factor(a, d),
        Factor(e, a),
        Factor('ok', c)
    )
    fs_2_product = BOR.from_args({}, {1, 100, 'test', 'ok'})

    terms = {
        fs_1: -1,
        fs_2: 1,
    }

    vector_1 = MPLVector(terms, MPLAlgebra.BOOLEAN, False)
    expectations = {
        vector_1: ~fs_1_product | fs_2_product
    }

    for input in expectations:
        expected = expectations[input]
        actual = eval_boolean_vector(input, cache)
        assert actual == expected, input