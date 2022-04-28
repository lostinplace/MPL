from textwrap import dedent
from typing import Dict, Tuple

from sympy import symbols

from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression
from mpl.Parser.ExpressionParsers.reference_expression_parser import Ref, Reference
from mpl.interpreter.conflict_resolution import identify_conflicts, get_resolutions, normalize_tracker
from mpl.interpreter.expression_evaluation.engine_context import EngineContext
from mpl.interpreter.expression_evaluation.entity_value import EntityValue, ev_fv, true_value
from mpl.interpreter.expression_evaluation.interpreters.target_exprression_interpreter import target_operations_dict
from mpl.interpreter.expression_evaluation.stack_management import symbolize_expression, \
    evaluate_symbolized_postfix_stack
from mpl.interpreter.rule_evaluation import RuleInterpretation, RuleInterpretationState
from mpl.lib import fs
from mpl.lib.context_tree.context_tree_implementation import tree_from_dict, reference_is_child_of_reference, \
    get_intermediate_child_ref, get_value, tree_to_dict, change_node, ContextTree


def diff_trackers(tracker1, tracker2):
    all_keys = set(tracker1.keys()) | set(tracker2.keys())
    result = {}
    for k in all_keys:
        if k == 'total':
            continue
        v1 = tracker1.get(k, 0)
        v2 = tracker2.get(k, 0)
        result[k] = (v1 or 0) - (v2 or 0)
    return result


def test_evaluating_query_expression_with_context_tree():
    from sympy import Rational
    input_dict = {
        Reference("a.b.c"): "value",
        Reference("a"): 'test',
        Reference("a.b.d"): 1,
        Reference("a.b.e"): 2,
        Reference("a.b.f"): None,
        Reference("test.final"): 3,
        Reference("test.*"): {},
        Reference("test.temporary"): 3,
    }

    expectations = {
        QueryExpression.parse("a.b.d +5"): EntityValue.from_value(6),
        QueryExpression.parse("a.b.e *5"): EntityValue.from_value(10),
        QueryExpression.parse("test.temporary /5"): EntityValue.from_value(Rational('3/5')),
        QueryExpression.parse("test.temporary ** 5"): EntityValue.from_value(243),
        QueryExpression.parse("test.final - 12"): EntityValue.from_value(-9),
    }

    for expression, expected in expectations.items():
        symbolized = symbolize_expression(expression)
        tree = ContextTree.from_dict(input_dict)
        context = EngineContext(tree)
        result = evaluate_symbolized_postfix_stack(symbolized, context)
        assert result == expected, expression


def test_evaluating_target_expression_with_context_tree():
    input_dict = {
        Reference("a.b.c"): ev_fv("value"),
        Reference("a"): ev_fv('test'),
        Reference("a.b.d"): ev_fv(1),
        Reference("a.b.e"): ev_fv(2),
        Reference("a.b.f"): ev_fv(),
        Reference("test.final"): ev_fv(3),
        Reference("test.*"): ev_fv(),
        Reference("test.temporary"): ev_fv(3),
    }

    expectations = {
        QueryExpression.parse("a.b.d & a.b"): ev_fv(Ref("a.b.d"), Ref("a.b"), 1, 2, symbols('`value`')),
        QueryExpression.parse("a.b.f ^ a.b.d-1"): ev_fv(Ref("a.b.f")),
    }

    for expression, expected in expectations.items():
        symbolized = symbolize_expression(expression, target_operations_dict)
        context = EngineContext.from_dict(input_dict)
        actual = evaluate_symbolized_postfix_stack(symbolized, context)
        assert actual.value == expected.value, expression


def test_reference_child_determination():
    expectations = {
        (Reference("a.b.c"), Reference("a.b.c")): 0,
        (Reference("a.b.c.d"), Reference("a.b.c")): 1,
        (Reference("a.b.d"), Reference("a.b.c")): -1,
        (Reference("a.b.c.d.e"), Reference("a.b.c")): 2,
        (Reference("a.b.c"), Reference("ROOT")): 3,
    }

    for (ref, parent_ref), expected_result in expectations.items():
        assert reference_is_child_of_reference(ref, parent_ref) == expected_result


def test_intermediate_child_generation():
    expectations = {
        (Reference("a.b.c"), Reference("a.b.c"), 0): Reference("a.b.c"),
        (Reference("a.b.c"), Reference("a.b.c.d.e"), 1): Reference("a.b.c.d"),
    }

    for (parent, target, steps), expected_result in expectations.items():
        assert get_intermediate_child_ref(parent, target, steps) == expected_result


def test_tree_creation_simple():
    input_dict = {
        Reference("a.b.c"): "value",
        Reference("a"): 'test',
        Reference("a.b.d"): 1,
        Reference("a.b.e"): 2,
        Reference("a.b.f"): None,
        Reference("test.final"): 3,
        Reference("test.*"): {},
        Reference("test.temporary"): 3,
    }
    expected_tree = \
    """
    ROOT: {}: {1, 2, 3, test, value}
    +a: {test}: {1, 2, test, value}
    ++a.b: {}: {1, 2, value}
    +++a.b.c: {value}: {value}
    +++a.b.d: {1}: {1}
    +++a.b.e: {2}: {2}
    +++a.b.f: {}: {}
    +test: {}: {3}
    ++test.final: {3}: {3}
    ++test.temporary: {3}: {3}
    """

    expected_tree_as_string = dedent(expected_tree).strip()

    actual_tree = tree_from_dict(input_dict)
    actual_tree_as_string = actual_tree.to_string()
    assert actual_tree_as_string == expected_tree_as_string


def test_retrieval_from_tree():
    input_dict = {
        Reference("a.b.c"): "value",
        Reference("a"): 'test',
        Reference("a.b.d"): 1,
        Reference("a.b.e"): 2,
        Reference("a.b.f"): None,
        Reference("test.final"): 3,
        Reference("test.*"): {},
        Reference("test.temporary"): 3,
    }
    tree = tree_from_dict(input_dict)

    expectations = {
        Reference("a.b.c"): "value",
        Reference("a"): {1, 2, 'test', 'value'},
        Reference("a.b.d"): 1,
        Reference("a.b.e"): 2,
        Reference("a.b.f"): None,
        Reference("test.final"): 3,
        Reference("test.*"): {},
        Reference("test.temporary"): 3,
        Reference("a.*"): {},
    }

    for ref, expected in expectations.items():
        actual = get_value(tree, ref)
        assert actual == EntityValue.from_value(expected)


def test_tree_to_dict():
    input_dict = {
        Reference("a.b.c"): "value",
        Reference("a"): 'test',
        Reference("a.b.d"): 1,
        Reference("a.b.e"): 2,
        Reference("a.b.f"): None,
        Reference("test.final"): 3,
        Reference("test.*"): {},
        Reference("test.temporary"): 3,
    }

    expected_dict = {
        Reference('ROOT'): EntityValue.from_value(frozenset({1, 2, 'test', 3, 'value'})),
        Reference('a'): EntityValue.from_value({2, 1, 'test', 'value'}),
        Reference('a.b'): EntityValue.from_value(frozenset({1, 'value', 2})),
        Reference('a.b.c'): EntityValue.from_value({'value'}),
        Reference('a.b.d'): EntityValue.from_value({1}),
        Reference('a.b.e'): EntityValue.from_value({2}),
        Reference('a.b.f'): EntityValue.from_value(frozenset()),
        Reference('test'): EntityValue.from_value(frozenset({3})),
        Reference('test.final'): EntityValue.from_value({3}),
        Reference('test.temporary'): EntityValue.from_value({3})
    }

    tree = tree_from_dict(input_dict)
    actual_dict = tree_to_dict(tree)
    assert actual_dict == expected_dict


def test_change_node():
    input_dict = {
        Reference("a.b.c"): "value",
        Reference("a"): 'test',
        Reference("a.b.d"): 1,
        Reference("a.b.e"): 2,
        Reference("a.b.f"): None,
        Reference("test.final"): 3,
        Reference("test.*"): {},
        Reference("test.temporary"): 3,
    }

    expectations = {
        (Reference("a.b.*"), 17): {
            Reference('ROOT'): EntityValue.from_value(frozenset({'test', 3})),
            Reference('a'): EntityValue.from_value({'test'}),
            Reference('a.b'): EntityValue(),
            Reference('a.b.*'): ev_fv(True),
            Reference('a.b.c'): ev_fv(),
            Reference('a.b.c.*'): true_value,
            Reference('a.b.d'): ev_fv(),
            Reference('a.b.d.*'): true_value,
            Reference('a.b.e'): ev_fv(),
            Reference('a.b.e.*'): true_value,
        },
        (Reference("a.b.d"), 13): {
            Reference('ROOT'): EntityValue.from_value(frozenset({13, 2, 'test', 3, 'value'})),
            Reference('a'): EntityValue.from_value({2, 13, 'test', 'value'}),
            Reference('a.b'): EntityValue.from_value(frozenset({13, 'value', 2})),
            Reference("a.b.d"): EntityValue.from_value(frozenset({13})),
        },
        (Reference("test"), frozenset()): {},
    }

    for (ref, change), expected_change in expectations.items():
        label = f"{ref} -> {change}"
        tree = tree_from_dict(input_dict)
        original_dict = tree_to_dict(tree)
        expected_dict = original_dict | expected_change
        expected_dict = {k: v for k, v in expected_dict.items() if not k.is_void}

        new_value = ev_fv(change)
        changes = change_node(tree, ref, new_value)
        assert changes == expected_change, label
        actual_dict = tree_to_dict(tree)
        assert actual_dict == expected_dict


def test_conflict_resolution_chain():
    def generate_conflict_dict(keys: set[str]) -> Dict[Reference, Tuple[EntityValue, EntityValue]]:
        return {key: (ev_fv(), EntityValue.from_value(1)) for key in keys}

    a = RuleInterpretation(
        RuleInterpretationState.APPLICABLE,
        generate_conflict_dict({'a', 'b', 'c'}),
        'a->b-c',
        fs(1),
        {
            Ref('a'): 'CONSUME',
            Ref('b'): 'CONSUME',
            Ref('c'): 'TARGET',
        }
    )
    b = RuleInterpretation(
        RuleInterpretationState.APPLICABLE,
        generate_conflict_dict({'c', 'd', 'e'}),
        'c->d->e',
        fs(1),
        {
            Ref('c'): 'CONSUME',
            Ref('d'): 'CONSUME',
            Ref('e'): 'TARGET',
        }
    )
    c = RuleInterpretation(
        RuleInterpretationState.APPLICABLE,
        generate_conflict_dict({'e', 'f', 'g'}),
        'e->f->g',
        fs(1),
        {
            Ref('e'): 'CONSUME',
            Ref('f'): 'CONSUME',
            Ref('g'): 'TARGET',
        }
    )
    d = RuleInterpretation(
        RuleInterpretationState.APPLICABLE,
        generate_conflict_dict({'h', 'i'}),
        'h->i',
        fs(1),
        {
            Ref('h'): 'CONSUME',
            Ref('i'): 'TARGET',
        }
    )
    e = RuleInterpretation(
        RuleInterpretationState.APPLICABLE,
        generate_conflict_dict({'a', 'c', 'e'}),
        'a->c->e',
        fs(1),
        {
            Ref('a'): 'CONSUME',
            Ref('c'): 'CONSUME',
            Ref('e'): 'TARGET',
        }
    )

    interpretations = frozenset({a, b, c, d, e})

    test_conflicts = identify_conflicts(interpretations)

    expectations = {
        fs(a, c, d): 1,
        fs(b, d): 1,
        fs(e, d): 1,
    }
    normalized_expectations = normalize_tracker(expectations)

    resolution_tracker = get_resolutions(test_conflicts, 5000)

    normalized_actual = normalize_tracker(resolution_tracker)

    diff = diff_trackers(normalized_expectations, normalized_actual)

    for k, v in diff.items():
        assert abs(v) < 0.05, f"{k} -> {v}"
