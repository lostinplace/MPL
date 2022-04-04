from sympy import symbols, N, Symbol

from mpl.Parser.ExpressionParsers.assignment_expression_parser import AssignmentExpression
from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression
from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference, Ref
from Tests import quick_parse
from mpl.Parser.ExpressionParsers.scenario_expression_parser import ScenarioExpression
from mpl.interpreter.expression_evaluation.engine_context import EngineContext

from mpl.interpreter.expression_evaluation.interpreters.create_expression_interpreter import \
    create_expression_interpreter
from mpl.interpreter.expression_evaluation.interpreters.query_expression_interpreter import QueryResult
from mpl.interpreter.expression_evaluation.interpreters.scenario_expression_interpreter import ScenarioResult
from mpl.interpreter.expression_evaluation.operators import query_operations_dict
from mpl.interpreter.expression_evaluation.stack_management import postfix, symbolize_postfix, symbolize_expression, \
    evaluate_symbolized_postfix_stack
from mpl.interpreter.expression_evaluation.types import ChangeLedgerRef

from mpl.lib import fs
from mpl.interpreter.expression_evaluation.entity_value import EntityValue, ev_fv
from mpl.lib.query_logic.expression_processing import entity_value_from_expression, ev_is_simplified, \
    expression_is_simplified


def opr(x):
    from mpl.interpreter.expression_evaluation.operators import query_operations_dict
    return query_operations_dict[x]


def test_postfix():
    from mpl.interpreter.expression_evaluation.operators import query_operations_dict

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

    for entry, expected in expectations.items():
        expr = quick_parse(QueryExpression, entry)
        actual = postfix(expr, operation_dict=query_operations_dict)
        assert actual == expected


def test_postfix_symbolization():
    # need to test the ability to convert a postfix stack into a collection of logical operations and symbols
    # this is a very important step in the evaluation of a query expression

    test_ref = Reference('test')
    test_two_ref = Reference('test two')

    expectations = {
        '!test & test two * 7': (test_ref.symbol, opr('!'), test_two_ref.symbol * 7, opr('&')),
    }

    for entry, expected in expectations.items():
        expr = quick_parse(QueryExpression, entry)
        tmp = postfix(expr, query_operations_dict)
        actual = symbolize_postfix(tmp)
        assert actual == expected


def test_eval_expr():
    from sympy import N
    red, black, uncolored = symbols('red black uncolored')

    context = {
        Reference('a'): ev_fv(5),
        Reference('b'): ev_fv('test'),
        Ref('state one'):
            ev_fv(5, -8.0, 'test'),
        Reference('bank'): ev_fv(3*red + 5*black),
        Reference('cost'): ev_fv(2 * red + 3 * uncolored),
        Ref('red', fs('symbol')): ev_fv(),
        Ref('black', fs('symbol')): ev_fv(),
        Ref('uncolored', fs('symbol')): ev_fv(),
    }

    expectations = {
        Ref('a').symbol + 3 + Ref('b').symbol: ev_fv(Symbol('`test`') + 8),
        Ref('a').symbol: ev_fv(5, Ref('a')),
        Ref('bank').symbol - Ref('cost').symbol: ev_fv(red + 5 * black - 3 * uncolored),
        Ref('state one').symbol - 5: ev_fv(N(-13.0), Symbol('`test`') - 5),
        Ref('a').symbol + 1: ev_fv(6),
    }

    context = EngineContext.from_dict(context)

    for entry, expected in expectations.items():
        actual = entity_value_from_expression(entry, context)
        assert actual == expected, entry


def test_query_expression_chain_evaluation():

    red, black, uncolored, a = symbols('red black uncolored a')
    context = {
        Reference('test'): 7,
        Reference('test two'): 196,
        Reference('bank'): ev_fv(3 * Ref('red') + 5 * Ref('black')),
        Reference('Hurt'): ev_fv(1),
        Reference('Turn Ended'): EntityValue( fs(1)),
        Reference('Turn Started'): ev_fv(),
        Reference('red', fs('symbol')): ev_fv(),
        Reference('a', fs('symbol')): ev_fv(),
        Reference('black', fs('symbol')): ev_fv(),
    }

    expectations = {
        'bank - (3 * red + 5 * black)': ev_fv(),
        '(a & test) ** 12': ev_fv(13841287201, a ** 12),
        '4+3*8**2/32+4**3/4-7': ev_fv(19.0),
        'bank & (bank - (5*black))': ev_fv(Ref('bank')) | ev_fv(3*red+5*black) | red * 3,
        'Hurt & <Turn Started>': ev_fv(),
        'Hurt & <Turn Ended>': ev_fv(1, Ref('Hurt'), Ref('Turn Ended')),
        '5--16': ev_fv(21),
        '5**2--16': ev_fv(41),
        '5**2.1--16': ev_fv(45.365473577200476),
        'bank ^ (test -7)': ev_fv(Ref('bank')) | ev_fv(3*red+5*black),
        'test -7 ^ test two': ev_fv(196.0, Ref('test two')),
        'test ** 12': ev_fv(13841287201),
        '4+3*8^2/32+4^3/4-7': ev_fv(-6.25),
        '!(test -7) ^ test two': ev_fv(),

    }

    context = EngineContext.from_dict(context)

    for entry, expected in expectations.items():
        expr = quick_parse(QueryExpression, entry)
        symbolized = symbolize_expression(expr)
        actual = evaluate_symbolized_postfix_stack(symbolized, context)
        assert actual == expected, entry


def test_query_expression_interpreter_complex():
    black, red, uncolored = symbols('black red uncolored')

    context_data = {
        Reference('test', None): 7,
        Reference('test two', None): 196,
        Reference('bank'): ev_fv(3 * Ref('red') + 5 * Ref('black')),
        Reference('Hurt'): ev_fv(1),
        Reference('Turn Ended'): ev_fv(1),
        Reference('Turn Started'): ev_fv(),
        Reference('void'): ev_fv(1),
        Reference('red', fs('symbol')): ev_fv(),
        Reference('black', fs('symbol')): ev_fv(),
    }

    context = EngineContext.from_dict(context_data)

    expectations = {
        'bank & (bank - (5*black))': QueryResult(
            ev_fv(Ref('bank'), red * 3) | context[Ref('bank')],
        ),
        '*': QueryResult(
            ev_fv(Ref('*')),
        ),
    }

    for entry, expected in expectations.items():
        expr = quick_parse(QueryExpression, entry)
        symbolized = symbolize_expression(expr)
        actual = create_expression_interpreter(expr)
        assert actual.symbolized == symbolized
        result = actual.interpret(context)
        assert result == expected


def test_assignment_expression_interpreter():
    context_data = {
        Reference('test'): ev_fv(7),
        Reference('test two'): ev_fv(196),
        Reference('test three'): ev_fv(5),
        Reference('bank'): ev_fv(3 * Ref('red') + 5 * Ref('black')),
        Reference('Hurt'): ev_fv(1),
        Reference('Turn Ended'): ev_fv(1),
        Reference('Turn Started'): ev_fv(),
        Reference('noise'): ev_fv(),
        Reference('red', fs('symbol')): ev_fv(),
        Reference('black', fs('symbol')): ev_fv(),
    }

    context = EngineContext.from_dict(context_data)

    expectations = {
        'bank = (bank - (5*black))': {
            Reference('bank'): ev_fv(3 * Ref('red')),
        },
        'noise = `safe`': {
            Reference('noise'): ev_fv(Symbol('`safe`')),
            Reference('noise.*'): ev_fv(),
        },
        'test three *= 7': {
            Reference('test three'): ev_fv(35),
        },
        'bank -= bank': {
            Reference('bank'): ev_fv(),
            Reference('bank.*'): ev_fv(1)
        },
        'test two /= 8.0': {
            Reference('test two'): ev_fv(N(24.5)),
        },
        'bank += 1': {
            Reference('bank'): ev_fv(3 * Ref('red') + 5 * Ref('black') + 1),
        },
        'test *= 7': {
            Reference('test'): ev_fv(49),
        },
    }

    for entry, expected in expectations.items():
        expr = quick_parse(AssignmentExpression, entry)

        interpreter = create_expression_interpreter(expr)
        actual = interpreter.interpret(context)

        assert actual.change == expected, entry


def test_scenario_expression_interpreter():
    context = {
        Reference('test'): 7,
        Reference('test two'): 196,
        Reference('test three'): fs(5),
        Reference('bank'): ev_fv(3 * Ref('red') + 5 * Ref('black')),
        Reference('Hurt'): ev_fv(1),
        Reference('Turn Ended'): ev_fv(1),
        Reference('Turn Started'): ev_fv(),
    }

    expectations = {
        '%{3}': ScenarioResult(ev_fv(3)),
        '%{bank - bank}': ScenarioResult(ev_fv()),
    }

    for entry, expected in expectations.items():
        expr = quick_parse(ScenarioExpression, entry)

        interpreter = create_expression_interpreter(expr)
        actual = interpreter.interpret(context)
        assert actual == expected


def test_expression_simplification_detector():
    black = symbols('black')
    white = symbols('white')
    context_data = {
        Ref('black', fs('symbol')): ev_fv(),
        Ref('white', fs('symbol')): ev_fv(),
        Ref('a'): ev_fv(1),
    }

    context = EngineContext.from_dict(context_data)

    expectations = {
        black + white * 3: True,
        Ref('a').symbol + black: False,
    }

    for expr, expected in expectations.items():
        assert expected == expression_is_simplified(expr, context)


def test_ev_simplification_detector():
    black = symbols('black')
    white = symbols('white')
    context_data = {
        Ref('black', fs('symbol')): ev_fv(),
        Ref('white', fs('symbol')): ev_fv(),
        Ref('a'): ev_fv(1),

    }

    context = EngineContext.from_dict(context_data)

    expectations = {
        ev_fv(black + white * 3, 1, Ref('a')): True,
        ev_fv(Ref('a').symbol + black): False,
        ev_fv(Ref('a').symbol + black, black + white * 3, 1): False,
        ev_fv(black, black + white * 3, 1): True,
        ev_fv(black, black + white * 3, 1, Ref('b').symbol): False,
    }

    for expr, expected in expectations.items():
        assert expected == ev_is_simplified(expr, context)
