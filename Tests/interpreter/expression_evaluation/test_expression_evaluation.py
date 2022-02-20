from sympy import symbols, N

from mpl.Parser.ExpressionParsers.assignment_expression_parser import AssignmentExpression
from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression
from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference, Ref
from Tests import quick_parse
from mpl.Parser.ExpressionParsers.scenario_expression_parser import ScenarioExpression
from mpl.interpreter.expression_evaluation.assignmment_expression_interpreter import AssignmentResult
from mpl.interpreter.expression_evaluation.query_expression_interpreter import postfix, symbolize_postfix, \
    evaluate_symbolized_postfix_stack, symbolize_expression, QueryResult
from mpl.interpreter.expression_evaluation import QueryExpressionInterpreter, create_expression_interpreter, query_operations_dict, \
    AssignmentExpressionInterpreter
from mpl.interpreter.expression_evaluation.scenario_expression_interpreter import ScenarioResult
from mpl.interpreter.reference_resolution.reference_graph_resolution import MPLEntityClass, MPLEntity
from mpl.lib import fs
from mpl.lib.query_logic import eval_expr_with_context



def opr(x):
    return query_operations_dict[x]


def test_postfix():

    expectations = {
        'first & !second ^ third - 4 * 5 | sixth':
            [Ref('first'), Ref('second'), opr('!'), Ref('third'), 4, 5, opr('*') , opr('-'), opr('^'), opr('&'), Ref('sixth'), opr('|')],
        'first & !(second ^ third) - 4 * 5 | sixth':
            [Ref('first'), Ref('second'), Ref('third'), opr('^'), opr('!'), 4, 5, opr('*'), opr('-'), opr('&'), Ref('sixth'), opr('|')],
        '!test & 3*7': [Reference('test'), opr('!'), 3, 7, opr('*'), opr('&')],
        '!test': [Reference('test'), opr('!')],
        '4+3*7': [4, 3, 7, opr('*'), opr('+')],

        '4+3': [4,3, opr('+')],
        '4+3 & test': [4, 3, opr('+'), Reference('test'), opr('&')],
    }

    for input, expected in expectations.items():
        expr = quick_parse(QueryExpression, input)
        actual = postfix(expr, operation_dict=query_operations_dict)
        assert actual == expected


def test_postfix_symbolization():
    # need to test the ability to convert a postfix stack into a collection of logical operations and symbols
    # this is a very important step in the evaluation of a query expression

    test_ref = Reference('test')
    test_two_ref = Reference('test two')

    expectations = {
        '!test & test two * 7': [test_ref.as_symbol(), opr('!'), test_two_ref.as_symbol() * 7, opr('&')],
    }

    for input, expected in expectations.items():
        expr = quick_parse(QueryExpression, input)
        tmp = postfix(expr, query_operations_dict)
        actual = symbolize_postfix(tmp)
        assert actual == expected


def test_eval_expr():
    from sympy import abc, N
    red, black, uncolored = symbols('red black uncolored')

    context = {
        Reference('a'): 5,
        Reference('b'): 'test',
        Ref('state one'):
            MPLEntity(0, 'state one', MPLEntityClass.MACHINE, fs(5, -8.0, 'test')),
        Reference('bank'): MPLEntity(1, 'bank', MPLEntityClass.VARIABLE, fs(3*red + 5*black)),
        Reference('cost'): 2 * red + 3 * uncolored,

    }

    expectations = {
        Ref('bank').as_symbol() - Ref('cost').as_symbol(): fs(red + 5 * black - 3 * uncolored),
        Ref('state one').as_symbol() - 5: fs(N(-13.0), symbols('test') - 5),
        Ref('a').as_symbol(): {5},
        abc.a + 1: fs(abc.a + 1),
        Ref('a').as_symbol() + 1: fs(6),
        Ref('a').as_symbol() + 3 + Ref('b').as_symbol(): fs(symbols('test') + 8),
    }

    for input, expected in expectations.items():
        actual = eval_expr_with_context(input, context)
        assert actual == expected, input


def test_query_expression_chain_evaluation():

    context = {
        Reference('test', None): 7,
        Reference('test two', None): 196,
        Reference('bank'): MPLEntity(1, 'bank', MPLEntityClass.VARIABLE, fs(3 * Ref('red') + 5 * Ref('black'))),
        Reference('Hurt'): MPLEntity(2, 'Hurt', MPLEntityClass.STATE, fs(1)),
        Reference('Turn Ended'): MPLEntity(3, 'Turn Ended', MPLEntityClass.TRIGGER, fs(1)),
        Reference('Turn Started'): MPLEntity(4, 'Turn Ended', MPLEntityClass.TRIGGER, fs()),
    }

    expectations = {
        'Hurt & <Turn Started>': fs(),
        'Hurt & <Turn Ended>': fs(context[Ref('Hurt')], context[Ref('Turn Ended')]),
        '5--16': fs(21),
        '5**2--16': fs(41),
        '5**2.1--16': fs(45.365473577200476),
        'bank & (bank - (5*black))': fs(context[Ref('bank')], Ref('red') * 3),
        'bank ^ (test -7)': fs(context[Ref('bank')]),
        'bank - (3 * red + 5 * black)': fs(),
        'test -7 ^ test two': fs(196.0),
        '(a & test) ** 12': fs(13841287201, Ref('a').as_symbol() ** 12),
        'test ** 12': fs(13841287201),
        '4+3*8^2/32+4^3/4-7': fs(-6.25),
        '4+3*8**2/32+4**3/4-7': fs(19.0),
        '!(test -7) ^ test two': fs(),

    }

    for input, expected in expectations.items():
        expr = quick_parse(QueryExpression, input)
        symbolized = symbolize_expression(expr)
        actual = evaluate_symbolized_postfix_stack(symbolized, context)
        assert actual == expected, input


def test_query_expression_interpreter_complex():
    context = {
        Reference('test', None): 7,
        Reference('test two', None): 196,
        Reference('bank'): MPLEntity(1, 'bank', MPLEntityClass.VARIABLE, fs(3 * Ref('red') + 5 * Ref('black'))),
        Reference('Hurt'): MPLEntity(2, 'Hurt', MPLEntityClass.STATE, fs(1)),
        Reference('Turn Ended'): MPLEntity(3, 'Turn Ended', MPLEntityClass.TRIGGER, fs(1)),
        Reference('Turn Started'): MPLEntity(4, 'Turn Ended', MPLEntityClass.TRIGGER, fs()),
        Reference('void'): MPLEntity(5, '*', MPLEntityClass.STATE, fs(1)),
    }

    expectations = {
        '*': QueryResult(
            fs(MPLEntity(5, '*', MPLEntityClass.STATE, fs(1))),
        ),
        'bank & (bank - (5*black))': QueryResult(
            fs(context[Ref('bank')], Ref('red') * 3)
        )
    }

    for input, expected in expectations.items():
        expr = quick_parse(QueryExpression, input)
        symbolized = symbolize_expression(expr)
        actual = create_expression_interpreter(expr)
        assert actual.symbolized == symbolized
        result = actual.interpret(context)
        assert result == expected


def test_assignment_expression_interpreter():
    context = {
        Reference('test'): 7,
        Reference('test two'): 196,
        Reference('test three'): fs(5),
        Reference('bank'): MPLEntity(1, 'bank', MPLEntityClass.VARIABLE, fs(3 * Ref('red') + 5 * Ref('black'))),
        Reference('Hurt'): MPLEntity(2, 'Hurt', MPLEntityClass.STATE, fs(1)),
        Reference('Turn Ended'): MPLEntity(3, 'Turn Ended', MPLEntityClass.TRIGGER, fs(1)),
        Reference('Turn Started'): MPLEntity(4, 'Turn Ended', MPLEntityClass.TRIGGER, fs()),
        Reference('noise'): MPLEntity(4, 'noise', MPLEntityClass.STATE, fs()),
    }

    expectations = {
        'noise = `safe`': {
            Reference('noise'): MPLEntity(4, 'noise', MPLEntityClass.STATE, fs('safe')),
        },
        'test three *= 7': {
            Reference('test three'): fs(35)
        },
        'bank -= bank': {
            Reference('bank'): MPLEntity(1, 'bank', MPLEntityClass.VARIABLE, fs())
        },
        'test two /= 8.0': {
            Reference('test two'): fs(N(24.5))
        },
        'bank = (bank - (5*black))': {
            Reference('bank'): MPLEntity(1, 'bank', MPLEntityClass.VARIABLE, fs(3 * Ref('red')))
        },
        'bank += 1': {
            Reference('bank'): MPLEntity(1, 'bank', MPLEntityClass.VARIABLE, fs(3 * Ref('red') + 5 * Ref('black') + 1))
        },
        'test *= 7': {
            Reference('test'): fs(49)
        },
    }

    for input, expected in expectations.items():
        expr = quick_parse(AssignmentExpression, input)

        interpreter = create_expression_interpreter(expr)
        actual = interpreter.interpret(context)
        assert actual == AssignmentResult(expected)


def test_scenario_expression_interpreter():
    context = {
        Reference('test'): 7,
        Reference('test two'): 196,
        Reference('test three'): fs(5),
        Reference('bank'): MPLEntity(1, 'bank', MPLEntityClass.VARIABLE, fs(3 * Ref('red') + 5 * Ref('black'))),
        Reference('Hurt'): MPLEntity(2, 'Hurt', MPLEntityClass.STATE, fs(1)),
        Reference('Turn Ended'): MPLEntity(3, 'Turn Ended', MPLEntityClass.TRIGGER, fs(1)),
        Reference('Turn Started'): MPLEntity(4, 'Turn Ended', MPLEntityClass.TRIGGER, fs()),
    }

    expectations = {
        '%{3}': ScenarioResult(fs(3)),
        '%{bank - bank}': ScenarioResult(fs()),
    }

    for input, expected in expectations.items():
        expr = quick_parse(ScenarioExpression, input)

        interpreter = create_expression_interpreter(expr)
        actual = interpreter.interpret(context)
        assert actual == expected