from mpl.Parser.ExpressionParsers.reference_expression_parser import Ref
from mpl.Parser.ExpressionParsers.rule_expression_parser import RuleClause, RuleExpression
from mpl.interpreter.expression_evaluation.engine_context import EngineContext
from mpl.interpreter.expression_evaluation.interpreters import ExpressionInterpreter
from mpl.interpreter.reference_resolution.reference_graph_resolution import MPLEntity, MPLEntityClass
from mpl.lib import fs


def test_context_generation_from_expressions():

    from Tests import quick_parse

    expectations = {
        'a & b | c + 3': {
            Ref('a'): MPLEntity(hash(Ref('a')), 'a', MPLEntityClass.STATE, frozenset()),
            Ref('b'): MPLEntity(hash(Ref('b')), 'b', MPLEntityClass.STATE, frozenset()),
            Ref('c'): MPLEntity(hash(Ref('c')), 'c', MPLEntityClass.STATE, frozenset()),
        },
        'test = b + 3 & `bart`': {
            Ref('test'): MPLEntity(hash(Ref('test')), 'test', MPLEntityClass.STATE, frozenset()),
            Ref('b'): MPLEntity(hash(Ref('b')), 'b', MPLEntityClass.STATE, frozenset()),
        },
        '%{a & b}': {
            Ref('a'): MPLEntity(hash(Ref('a')), 'a', MPLEntityClass.STATE, frozenset()),
            Ref('b'): MPLEntity(hash(Ref('b')), 'b', MPLEntityClass.STATE, frozenset()),
        },
    }

    for expr_input, expected in expectations.items():
        clause = quick_parse(RuleClause, expr_input)
        expression = clause.expression
        interpreter = ExpressionInterpreter.from_expression(expression)
        references = interpreter.references
        actual = EngineContext.from_references(references)
        assert actual == expected


def test_context_generation_from_rules():
    from Tests import quick_parse
    from mpl.interpreter.rule_evaluation import RuleInterpreter

    expectations = {
        'a & b -> c -> d': {
            Ref('a'): MPLEntity(hash(Ref('a')), 'a', MPLEntityClass.STATE, frozenset()),
            Ref('b'): MPLEntity(hash(Ref('b')), 'b', MPLEntityClass.STATE, frozenset()),
            Ref('c'): MPLEntity(hash(Ref('c')), 'c', MPLEntityClass.STATE, frozenset()),
            Ref('d'): MPLEntity(hash(Ref('d')), 'd', MPLEntityClass.STATE, frozenset()),
        },
    }

    for rule_input, expected in expectations.items():
        rule = quick_parse(RuleExpression, rule_input)
        interpreter = RuleInterpreter.from_expression(rule)
        actual = EngineContext.from_interpreter(interpreter)
        assert actual == expected


def test_context_activation():
    from Tests import quick_parse

    expectations = {
        ('test  & something complex ^ `with a string` + ok', fs('test', 'something complex'), None): {
            Ref('test'): MPLEntity(hash(Ref('test')), 'test', MPLEntityClass.STATE, frozenset([hash(Ref('test'))])),
            Ref('something complex'):
                MPLEntity(
                    hash(Ref('something complex')),
                    'something complex',
                    MPLEntityClass.STATE, frozenset([hash(Ref('something complex'))])
                ),
            Ref('ok'): MPLEntity(hash(Ref('ok')), 'ok', MPLEntityClass.STATE, frozenset()),
        },
        ('a & b', 'a', None): {
            Ref('a'): MPLEntity(hash(Ref('a')), 'a', MPLEntityClass.STATE, frozenset([hash(Ref('a'))])),
            Ref('b'): MPLEntity(hash(Ref('b')), 'b', MPLEntityClass.STATE, frozenset()),
        },
        ('test  & something ^ not me', Ref('test'), None): {
            Ref('test'): MPLEntity(hash(Ref('test')), 'test', MPLEntityClass.STATE, frozenset([hash(Ref('test'))])),
            Ref('something'): MPLEntity(hash(Ref('something')), 'something', MPLEntityClass.STATE, frozenset()),
            Ref('not me'): MPLEntity(hash(Ref('not me')), 'not me', MPLEntityClass.STATE, frozenset()),
        },
        ('test  & something ^ not me | complicated', fs(Ref('test'), 'complicated'), 'ok'): {
            Ref('test'): MPLEntity(hash(Ref('test')), 'test', MPLEntityClass.STATE, fs('ok')),
            Ref('something'): MPLEntity(hash(Ref('something')), 'something', MPLEntityClass.STATE, frozenset()),
            Ref('not me'): MPLEntity(hash(Ref('not me')), 'not me', MPLEntityClass.STATE, frozenset()),
            Ref('complicated'): MPLEntity(hash(Ref('complicated')), 'complicated', MPLEntityClass.STATE, fs('ok')),
        },
    }

    for (expr_input, ref_input, ref_value), expected in expectations.items():

        clause = quick_parse(RuleClause, expr_input)
        expression = clause.expression
        interpreter = ExpressionInterpreter.from_expression(expression)
        references = interpreter.references
        context = EngineContext.from_references(references)
        actual = context.activate(ref_input, ref_value)
        assert actual == expected