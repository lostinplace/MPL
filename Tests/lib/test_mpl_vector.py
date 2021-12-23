from Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpression
from Parser.ExpressionParsers.reference_expression_parser import Reference
from Tests import quick_parse
from lib.mpl_vector import MPLVector, fs, TK, qv, to_vector, vector_to_string, tk_set_times_tk_set, to_mpl_vector, \
    eval_mpl_vector


def test_mpl_vector_from_arithmetic_expression():
    Ref=Reference
    expectations = {
        '11*test^(3*base) + 19*x^13 -12^2': MPLVector({
            fs(
                TK(Ref('test'), qv('3*base')),
            ): 11,
            fs(TK(Ref('x'), 13)): 19,
            fs(TK(1, 1)): -144,
        }),
        '3*base': MPLVector({
            fs(
                TK(Ref('base'), 1),
            ): 3,
        }),

        '5 / test^3*base - -16*x/4 -120.2': MPLVector({
            fs(
                TK(Ref('test'), -3),
                TK(Ref('base'), 1),
            ): 5.0,
            fs(TK(Ref('x'), 1)): 4.0,
            fs(TK(1, 1)): -120.2,
        }),
        'a^2 + b +3 ': MPLVector({
            fs(TK(Ref('b'), 1)): 1,
            fs(TK(1, 1)): 3,
            fs(TK(Ref('a'), 2)): 1,
        }),
        '5*test^3*base - 17*x +12': MPLVector({
            fs(
                TK(Ref('test'), 3),
                TK(Ref('base'), 1),
            ): 5,
            fs(TK(Ref('x'), 1)): -17,
            fs(TK(1, 1)): 12,
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


def test_tk_set_times_tk_set():
    set_a = fs(TK('a', 2), TK('b', 2))
    set_a_times_set_a = fs(TK('a', 4), TK('b', 4))

    expectations = {
        (set_a, set_a): set_a_times_set_a
    }

    for input in expectations:
        actual = tk_set_times_tk_set(*input)
        expected = expectations[input]
        assert actual == expected


def test_vector_exponentiation():
    vec1 = MPLVector({
        fs(TK('a', 3)): 5,
    })

    vec1_up_2 = MPLVector({
        fs(TK('a', 6)): 25,
    })

    assert vec1 ** 2 ==  vec1_up_2

    vec1_up_test_sub_1 = MPLVector({
        fs(TK('test', 1)): 3
    })

    vec1_up_test = MPLVector({
        fs(
            TK('a', vec1_up_test_sub_1),
            TK(5, 'test')
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
    assert a == MPLVector({fs(TK(7, 'c')): 1})
    b = vec_c ** 'c'
    assert b == MPLVector({fs(TK('c', 'c')): 1})
    ab = a*b
    assert ab == MPLVector({fs(TK(7,'c'), TK('c','c')):1})
    vec2_1upc = (to_mpl_vector(7) ** 'c') * (vec_c ** 'c')
    vec2_2upc = to_mpl_vector(11) ** 'c'
    vec_2upc_expected = vec1_upc + vec2_1upc + vec2_2upc
    vec2_upc_actual = vec_2 ** 'c'
    assert vec2_upc_actual == vec_2upc_expected


def test_vector_multiplication():
    vec1 = MPLVector({
        fs(TK('a', 2)): 1,
    })
    vec1tvec1 = MPLVector({
        fs(TK('a', 4)): 1,
    })
    vec1t6 = MPLVector({
        fs(TK('a', 2)): 6,
    })
    vec1t_test_me = MPLVector({
        fs(TK('a', 2), TK('test me', 1)): 1,
    })
    vec2 = MPLVector({
        fs(TK('b', 2)): 2,
    })
    vec1tvec2 = MPLVector({
        fs(TK('a', 2), TK('b', 2)): 2,
    })
    vec3 = MPLVector({
        fs(TK('a', 3)): 1,
        fs(TK('a', 2)): 1,
        fs(TK('b', 2), TK('a', 1)): 2,
    })
    vec3tvec3 = MPLVector({
        fs(TK('a', 6)): 1,
        fs(TK('a', 5)): 2,
        fs(TK('a', 4)): 1,
        fs(TK('a', 3), TK('b', 2)): 4,
        fs(TK('a', 4), TK('b', 2)): 4,
        fs(TK('a', 2), TK('b', 4)): 4,
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
        fs(TK('a', 2)): 1,
    })
    vec1pvec1 = MPLVector({
        fs(TK('a', 2)): 2,
    })
    vec1p6 = MPLVector({
        fs(TK('a', 2)): 1,
        fs(TK(1, 1)): 6,
    })
    vec1p_test_me = MPLVector({
        fs(TK('a', 2)): 1,
        fs(TK('test me', 1)): 1,
    })
    vec2 = MPLVector({
        fs(TK('b', 2)): 2,
    })
    vec1pvec2 =MPLVector({
        fs(TK('a', 2)): 1,
        fs(TK('b', 2)): 2,
    })
    vec3 = vec1pvec2 * TK('a', 1)
    vec3pvec1 = MPLVector({
        fs(TK('a', 2)): 1,
        fs(TK('a', 3)): 1,
        fs(TK('b', 2), TK('a', 1)): 2,
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
        TK('a', 2) ** 3: TK('a', 6),
        TK('a', 1) ** 'test': TK('a', 'test'),
        TK('a', 5) ** TK('a', 5):
            TK(
                'a',
                MPLVector(
                    {fs(TK('a', 5)): 5}
                )
            ),
    }

    for actual in expectations:
        assert actual == expectations[actual]


def test_tk_addition():
    expectations = {
        TK('a', 1) + MPLVector({
            fs(TK('a', 1)): 5,
            fs(TK('a', 2), TK('b', 2)): 7,
        }): MPLVector({
            fs(TK('a', 1)): 6,
            fs(TK('a', 2), TK('b', 2)): 7,
        }),
        TK('a', 1) + TK('a', 1): MPLVector(
            {fs(TK('a', 1)): 2}
        ),
        TK('a', 1) + TK('a', 2): MPLVector(
            {
                fs(TK('a', 1)): 1,
                fs(TK('a', 2)): 1,
            }
        ),
        TK('a', 1) + TK('a', 2): MPLVector(
            {
                fs(TK('a', 1)): 1,
                fs(TK('a', 2)): 1,
            }
        ),
        TK('a', 1) + 5: MPLVector(
            {
                fs(TK('a', 1)): 1,
                fs(TK(1, 1)): 5,
            }
        ),
    }

    for actual in expectations:
        assert actual == expectations[actual]


def test_tk_multiplication():

    expectations = {
        TK('a', 1) * MPLVector({
            fs(TK('a', 1)): 5,
            fs(TK('a', 2), TK('b', 2)): 7,
        }): MPLVector({
            fs(TK('a', 2)): 5,
            fs(TK('a', 3), TK('b', 2)): 7,
        }),
        TK('a', 1) * TK('a', 1): MPLVector(
            {fs(TK('a', 2)): 1}
        ),
        TK('a', 1) * TK('b', 1): MPLVector({
            fs(TK('a', 1), TK('b', 1)): 1,
        }),
        TK('a', 1) * 5: MPLVector({
            fs(TK('a', 1)): 5,
        }),
    }
    for actual in expectations:
        assert actual == expectations[actual]


def test_mpl_vector_simplification():
    ref_cache = {
        Reference('test', None): 12
    }

    expectations = {
        qv('144 * 32'):  144 * 32,
        qv('144 - test ^ 2'): 0,
        qv('5*x') - qv('5*x'): 0
    }

    for e in expectations:
        expected = expectations[e]
        actual = eval_mpl_vector(e, ref_cache)
        assert actual == expected


