from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression
from mpl.Parser.ExpressionParsers.reference_expression_parser import Ref
from mpl.Parser.ExpressionParsers.rule_expression_parser import RuleExpression
from mpl.interpreter.expression_evaluation.engine_context import EngineContext
from mpl.interpreter.expression_evaluation.interpreters import ExpressionInterpreter

from mpl.lib import fs
from mpl.interpreter.expression_evaluation.entity_value import EntityValue


def test_context_generation_from_expressions():

    from Tests import quick_parse

    expectations = {
        'a & b | c + 3': {
            Ref('a'): EntityValue(frozenset()),
            Ref('b'): EntityValue(frozenset()),
            Ref('c'): EntityValue(frozenset()),
        },
        'test = b + 3 & `bart`': {
            Ref('test'): EntityValue(frozenset()),
            Ref('b'): EntityValue(frozenset()),
        },
        '%{a & b}': {
            Ref('a'): EntityValue(frozenset()),
            Ref('b'): EntityValue(frozenset()),
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
            Ref('a'): EntityValue(frozenset()),
            Ref('b'): EntityValue(frozenset()),
            Ref('c'): EntityValue(frozenset()),
            Ref('d'): EntityValue(frozenset()),
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
        ('test  & something complex ^ `with a string` + ok', fs('something complex'), None): {
            Ref('test'): EntityValue(frozenset([hash(Ref('test'))])),
            Ref('something complex'):
                EntityValue.from_value(hash(Ref('something complex'))),
            Ref('ok'): EntityValue(frozenset()),
        },
        ('a & b', 'a', None): {
            Ref('a'): EntityValue(frozenset([hash(Ref('a'))])),
            Ref('b'): EntityValue(frozenset()),
        },
        ('test  & something ^ not me', Ref('test'), None): {
            Ref('test'): EntityValue(frozenset([hash(Ref('test'))])),
            Ref('something'): EntityValue(frozenset()),
            Ref('not me'): EntityValue(frozenset()),
        },
        ('test  & something ^ not me | complicated', fs(Ref('test'), 'complicated'), 'ok'): {
            Ref('test'): EntityValue(fs('ok')),
            Ref('something'): EntityValue(frozenset()),
            Ref('not me'): EntityValue(frozenset()),
            Ref('complicated'): EntityValue(fs('ok')),
        },
    }

    for (expr_input, ref_input, ref_value), expected in expectations.items():

        expression = quick_parse(QueryExpression, expr_input)
        interpreter = ExpressionInterpreter.from_expression(expression)
        references = interpreter.references
        context = EngineContext.from_references(references)
        actual = context.activate(ref_input, ref_value)
        assert actual == expected