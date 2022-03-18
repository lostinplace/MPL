from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression
from mpl.Parser.ExpressionParsers.reference_expression_parser import Ref
from mpl.Parser.ExpressionParsers.rule_expression_parser import RuleExpression
from mpl.interpreter.expression_evaluation.engine_context import EngineContext
from mpl.interpreter.expression_evaluation.interpreters import ExpressionInterpreter
from mpl.interpreter.reference_resolution.mpl_entity import MPLEntity
from mpl.lib import fs


def test_context_generation_from_expressions():

    from Tests import quick_parse

    expectations = {
        'a & b | c + 3': {
            Ref('a'): MPLEntity('a', frozenset()),
            Ref('b'): MPLEntity('b', frozenset()),
            Ref('c'): MPLEntity('c', frozenset()),
        },
        'test = b + 3 & `bart`': {
            Ref('test'): MPLEntity('test', frozenset()),
            Ref('b'): MPLEntity('b', frozenset()),
        },
        '%{a & b}': {
            Ref('a'): MPLEntity('a', frozenset()),
            Ref('b'): MPLEntity('b', frozenset()),
        },
    }

    for expr_input, expected in expectations.items():
        rule = quick_parse(RuleExpression, expr_input)
        expression = rule.clauses[0]
        interpreter = ExpressionInterpreter.from_expression(expression)
        references = interpreter.references
        actual = EngineContext.from_references(references)
        assert actual == expected


def test_context_generation_from_rules():
    from Tests import quick_parse
    from mpl.interpreter.rule_evaluation import RuleInterpreter

    expectations = {
        'a & b -> c -> d': {
            Ref('a'): MPLEntity('a', frozenset()),
            Ref('b'): MPLEntity('b', frozenset()),
            Ref('c'): MPLEntity('c', frozenset()),
            Ref('d'): MPLEntity('d', frozenset()),
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
            Ref('test'): MPLEntity('test', frozenset([hash(Ref('test'))])),
            Ref('something complex'):
                MPLEntity(
                    'something complex',
                    frozenset([hash(Ref('something complex'))])
                ),
            Ref('ok'): MPLEntity('ok', frozenset()),
        },
        ('a & b', 'a', None): {
            Ref('a'): MPLEntity('a', frozenset([hash(Ref('a'))])),
            Ref('b'): MPLEntity('b', frozenset()),
        },
        ('test  & something ^ not me', Ref('test'), None): {
            Ref('test'): MPLEntity('test', frozenset([hash(Ref('test'))])),
            Ref('something'): MPLEntity('something', frozenset()),
            Ref('not me'): MPLEntity('not me', frozenset()),
        },
        ('test  & something ^ not me | complicated', fs(Ref('test'), 'complicated'), 'ok'): {
            Ref('test'): MPLEntity('test', fs('ok')),
            Ref('something'): MPLEntity('something', frozenset()),
            Ref('not me'): MPLEntity('not me', frozenset()),
            Ref('complicated'): MPLEntity('complicated', fs('ok')),
        },
    }

    for (expr_input, ref_input, ref_value), expected in expectations.items():

        expression = quick_parse(QueryExpression, expr_input)
        interpreter = ExpressionInterpreter.from_expression(expression)
        references = interpreter.references
        context = EngineContext.from_references(references)
        actual = context.activate(ref_input, ref_value)
        assert actual == expected