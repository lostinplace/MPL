from mpl.Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpression
from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference
from Tests import quick_parse
from mpl.lib.mpl_vector import MPLVector, fs, Factor, qv, to_vector, vector_to_string, to_mpl_vector, \
    eval_mpl_vector


def test_mpl_vector_from_arithmetic_expression():
    Ref=Reference
    expectations = {
        '11*test^(3*base) + 19*x^13 -12^2': MPLVector({
            fs(
                Factor(Ref('test'), qv('3*base')),
            ): 11,
            fs(Factor(Ref('x'), 13)): 19,
            fs(Factor(1, 1)): -144,
        }),
        '3*base': MPLVector({
            fs(
                Factor(Ref('base'), 1),
            ): 3,
        }),

        '5 / test^3*base - -16*x/4 -120.2': MPLVector({
            fs(
                Factor(Ref('test'), -3),
                Factor(Ref('base'), 1),
            ): 5.0,
            fs(Factor(Ref('x'), 1)): 4.0,
            fs(Factor(1, 1)): -120.2,
        }),
        'a^2 + b +3 ': MPLVector({
            fs(Factor(Ref('b'), 1)): 1,
            fs(Factor(1, 1)): 3,
            fs(Factor(Ref('a'), 2)): 1,
        }),
        '5*test^3*base - 17*x +12': MPLVector({
            fs(
                Factor(Ref('test'), 3),
                Factor(Ref('base'), 1),
            ): 5,
            fs(Factor(Ref('x'), 1)): -17,
            fs(Factor(1, 1)): 12,
        }),
    }

    for e in expectations:
        expr = quick_parse(ArithmeticExpression, e)
        actual = to_vector(expr)
        expected = expectations[e]

        # assert actual == expected
        actual_string = vector_to_string(actual)
        expected_string = vector_to_string(expected)
        assert actual_string == expected_string


def test_vector_exponentiation():
    vec1 = MPLVector({
        fs(Factor('a', 3)): 5,
    })

    vec1_up_2 = MPLVector({
        fs(Factor('a', 6)): 25,
    })

    assert vec1 ** 2 ==  vec1_up_2

    vec1_up_test_sub_1 = MPLVector({
        fs(Factor('test', 1)): 3
    })

    vec1_up_test = MPLVector({
        fs(
            Factor('a', vec1_up_test_sub_1),
            Factor(5, 'test')
        ): 1,
    })

    assert vec1 ** 'test' == vec1_up_test

    vec_c = to_mpl_vector('c')

    vec_2_1 = to_mpl_vector(7) * 'c'
    vec_2_2 = to_mpl_vector(11)
    vec_2 = vec1 + vec_2_1 + vec_2_2

    v1 = (to_mpl_vector(5) ** 'c')
    v2 = to_mpl_vector('a') ** (vec_c * 3)

    vec1_upc = v1 * v2
    a = to_mpl_vector(7) ** 'c'
    assert a == MPLVector({fs(Factor(7, 'c')): 1})
    b = vec_c ** 'c'
    assert b == MPLVector({fs(Factor('c', 'c')): 1})
    ab = a*b
    assert ab == MPLVector({fs(Factor(7, 'c'), Factor('c', 'c')):1})
    vec2_1upc = (to_mpl_vector(7) ** 'c') * (vec_c ** 'c')
    vec2_2upc = to_mpl_vector(11) ** 'c'
    vec_2upc_expected = vec1_upc + vec2_1upc + vec2_2upc
    vec2_upc_actual = vec_2 ** 'c'
    assert vec2_upc_actual == vec_2upc_expected


def test_vector_multiplication():
    vec1 = MPLVector({
        fs(Factor('a', 2)): 1,
    })
    vec1tvec1 = MPLVector({
        fs(Factor('a', 4)): 1,
    })
    vec1t6 = MPLVector({
        fs(Factor('a', 2)): 6,
    })
    vec1t_test_me = MPLVector({
        fs(Factor('a', 2), Factor('test me', 1)): 1,
    })
    vec2 = MPLVector({
        fs(Factor('b', 2)): 2,
    })
    vec1tvec2 = MPLVector({
        fs(Factor('a', 2), Factor('b', 2)): 2,
    })
    vec3 = MPLVector({
        fs(Factor('a', 3)): 1,
        fs(Factor('a', 2)): 1,
        fs(Factor('b', 2), Factor('a', 1)): 2,
    })
    vec3tvec3 = MPLVector({
        fs(Factor('a', 6)): 1,
        fs(Factor('a', 5)): 2,
        fs(Factor('a', 4)): 1,
        fs(Factor('a', 3), Factor('b', 2)): 4,
        fs(Factor('a', 4), Factor('b', 2)): 4,
        fs(Factor('a', 2), Factor('b', 4)): 4,
    })

    expectations = {
        vec1 * 6: vec1t6,
        vec1 * 'test me': vec1t_test_me,
        vec1 * vec1: vec1tvec1,
        vec1 * vec2: vec1tvec2,
        vec3 * vec3: vec3tvec3,
    }

    for actual in expectations:
        expected = expectations[actual]
        assert actual == expected


def test_vector_addition():
    vec1 = MPLVector({
        fs(Factor('a', 2)): 1,
    })
    vec1pvec1 = MPLVector({
        fs(Factor('a', 2)): 2,
    })
    vec1p6 = MPLVector({
        fs(Factor('a', 2)): 1,
        fs(Factor(1, 1)): 6,
    })
    vec1p_test_me = MPLVector({
        fs(Factor('a', 2)): 1,
        fs(Factor('test me', 1)): 1,
    })
    vec2 = MPLVector({
        fs(Factor('b', 2)): 2,
    })
    vec1pvec2 =MPLVector({
        fs(Factor('a', 2)): 1,
        fs(Factor('b', 2)): 2,
    })
    vec3 = vec1pvec2 * Factor('a', 1)
    vec3pvec1 = MPLVector({
        fs(Factor('a', 2)): 1,
        fs(Factor('a', 3)): 1,
        fs(Factor('b', 2), Factor('a', 1)): 2,
    })

    expectations = {
        vec1 + 6: vec1p6,
        vec1 + 'test me': vec1p_test_me,
        vec1 + vec1: vec1pvec1,
        vec1 + vec2: vec1pvec2,
        vec3 + vec1: vec3pvec1,
    }

    for actual in expectations:
        expected = expectations[actual]
        assert actual == expected


def test_tk_exponentiation():
    expectations = {
        Factor('a', 2) ** 3: Factor('a', 6),
        Factor('a', 1) ** 'test': Factor('a', 'test'),
        Factor('a', 5) ** Factor('a', 5):
            Factor(
                'a',
                MPLVector(
                    {fs(Factor('a', 5)): 5}
                )
            ),
    }

    for actual in expectations:
        assert actual == expectations[actual]


def test_tk_addition():
    expectations = {
        Factor('a', 1) + MPLVector({
            fs(Factor('a', 1)): 5,
            fs(Factor('a', 2), Factor('b', 2)): 7,
        }): MPLVector({
            fs(Factor('a', 1)): 6,
            fs(Factor('a', 2), Factor('b', 2)): 7,
        }),
        Factor('a', 1) + Factor('a', 1): MPLVector(
            {fs(Factor('a', 1)): 2}
        ),
        Factor('a', 1) + Factor('a', 2): MPLVector(
            {
                fs(Factor('a', 1)): 1,
                fs(Factor('a', 2)): 1,
            }
        ),
        Factor('a', 1) + Factor('a', 2): MPLVector(
            {
                fs(Factor('a', 1)): 1,
                fs(Factor('a', 2)): 1,
            }
        ),
        Factor('a', 1) + 5: MPLVector(
            {
                fs(Factor('a', 1)): 1,
                fs(Factor(1, 1)): 5,
            }
        ),
    }

    for actual in expectations:
        assert actual == expectations[actual]


def test_tk_multiplication():

    expectations = {
        Factor('a', 1) * MPLVector({
            fs(Factor('a', 1)): 5,
            fs(Factor('a', 2), Factor('b', 2)): 7,
        }): MPLVector({
            fs(Factor('a', 2)): 5,
            fs(Factor('a', 3), Factor('b', 2)): 7,
        }),
        Factor('a', 1) * Factor('a', 1): MPLVector(
            {fs(Factor('a', 2)): 1}
        ),
        Factor('a', 1) * Factor('b', 1): MPLVector({
            fs(Factor('a', 1), Factor('b', 1)): 1,
        }),
        Factor('a', 1) * 5: MPLVector({
            fs(Factor('a', 1)): 5,
        }),
    }
    for actual in expectations:
        assert actual == expectations[actual]


def test_mpl_vector_simplification():
    ref_cache = {
        Reference('test', None): 12,
        Reference('nested', None): qv('test * 3')
    }

    expectations = {
        qv('144 - test ^ 2'): 0,
        qv('144 * 32'):  144 * 32,
        qv('5*x') - qv('5*x'): 0,
        qv('nested ^ 0.5') : 6
    }

    for e in expectations:
        expected = expectations[e]
        actual = eval_mpl_vector(e, ref_cache)
        assert actual == expected


def test_sympy():
    from sympy import Symbol, Function, symbols, Eq, cse, N, Gt, Add
    red, black, uncolored = symbols('red black uncolored')
    f, g = symbols('f g', cls=Function)
    t = symbols('test__filter_123')

    expr_1 = 5*red + 3*black
    expr_2 = 2*red + uncolored
    expr_3 = expr_1 - expr_2
    coeffs = expr_3.as_coefficients_dict()
    expr_4 = Eq(expr_3, 7*uncolored)
    out = cse(expr_3)
    terms = expr_3.as_ordered_terms()
    term_0 = terms[0]

    print(expr_3)
    pass



