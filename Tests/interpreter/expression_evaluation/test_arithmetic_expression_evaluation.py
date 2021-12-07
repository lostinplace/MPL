from Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpression
from Parser.ExpressionParsers.reference_expression_parser import Reference
from Tests import quick_parse
from interpreter.expression_evaluation.arithmetic_expression_interpreter import postfix, eval_postfix, \
    evaluate_expression
from interpreter.reference_resolution.reference_graph_resolution import MPLEntity, MPLEntityClass, MPLValueType


def test_postfix():

    cache = {
        Reference('test', None): MPLEntity(0, 'test', MPLEntityClass.VARIABLE, MPLValueType.NUMBER, 7),
        Reference('test 2', None): MPLEntity(0, 'test 2', MPLEntityClass.VARIABLE, MPLValueType.NUMBER, 196),
    }

    expectations = {
        '4+3*8^2/32+4^3/4-7': 19,
        '1+(test-3)*4': 17,
        '9- 4 + -5.12 * (test 2 ^ 0.5 + 7) / test': -10.36,
    }

    for input, expected in expectations.items():
        expr = quick_parse(ArithmeticExpression, input)
        postfix_queue = postfix(expr)
        actual = eval_postfix(postfix_queue, cache)
        assert actual == expected


def test_postfix_evaluation():
    expectations = {
        '4+3*8^2/32+4^3/4-7': [
            4, 3, 8, 2, '^', '*', 32, '/', '+', 4, 3, '^', 4, '/', '+', 7, '-'
        ],
        '1+(test-3)*4': [
            1, Reference('test', None), 3, '-', 4, '*', '+'
        ],

    }

    for input, expected in expectations.items():
        expr = quick_parse(ArithmeticExpression, input)
        actual = postfix(expr)
        assert actual == expected


def test_expression_evaluation():
    cache = {
        Reference('x', None): 5,
        Reference('y', None): 7,
        Reference('a', None): 3,
        Reference('c', None): 12,
    }

    expectations = {
        "2^((-1+6)/4)*7/-9/3": -0.6166259114828924,
        '3*x^2 + (5^y + (a+19) -c) ^ 3': 477020287110450,
        '12.0/-13^14.15--16': (16.000000000000004-9.417368741536094e-16j),
        '-149.012': -149.012,
    }

    for input, expected in expectations.items():
        expr = quick_parse(ArithmeticExpression, input)
        actual = evaluate_expression(expr, cache)

        assert actual == expected