from random import Random
from textwrap import dedent
from typing import Dict, List, FrozenSet

from mpl.Parser.ExpressionParsers import Reference
from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression
from mpl.Parser.ExpressionParsers.reference_expression_parser import Ref
from mpl.interpreter.conflict_resolution import RuleConflict, resolve_conflicts, identify_conflicts, get_resolutions, \
    normalize_tracker
from mpl.interpreter.expression_evaluation.entity_value import EntityValue
from mpl.interpreter.expression_evaluation.interpreters import target_operations_dict
from mpl.interpreter.expression_evaluation.stack_management import symbolize_expression, \
    evaluate_symbolized_postfix_stack
from mpl.interpreter.rule_evaluation import RuleInterpretation, RuleInterpretationState
from mpl.lib import fs
from mpl.lib.context_tree.context_tree_implementation import tree_from_dict, reference_is_child_of_reference, \
    get_intermediate_child_ref, get_value, tree_to_dict, change_node


def diff_trackers(tracker1, tracker2):
    all_keys = set(tracker1.keys()) | set(tracker2.keys())
    result = {}
    for k in all_keys:
        if k =='total':
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
        context = tree_from_dict(input_dict)
        result = evaluate_symbolized_postfix_stack(symbolized, context)
        assert result == expected, expression


def test_evaluating_target_expression_with_context_tree():
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
        QueryExpression.parse("a.b.d & a.b"): EntityValue.from_value({Ref("a.b.d"), Ref("a.b"), 1, 2, 'value'}),
        QueryExpression.parse("a.b.f ^ a.b.d-1"): EntityValue.from_value({Ref("a.b.f")}),
        QueryExpression.parse("a.b.f | test.*"): EntityValue.from_value({Ref("a.b.f"), Ref("test.*")}),
    }

    for expression, expected in expectations.items():
        symbolized = symbolize_expression(expression, target_operations_dict)
        context = tree_from_dict(input_dict)
        result = evaluate_symbolized_postfix_stack(symbolized, context, True)
        assert result == expected, expression


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
        Reference('a.b.f.*'): EntityValue.from_value({1}),
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
        (Reference("a.b.d"), 13): {
            Reference('ROOT'): EntityValue.from_value(frozenset({13, 2, 'test', 3, 'value'})),
            Reference('a'): EntityValue.from_value({2, 13, 'test', 'value'}),
            Reference('a.b'): EntityValue.from_value(frozenset({13, 'value', 2})),
            Reference("a.b.d"): EntityValue.from_value(frozenset({13})),
        },
        (Reference("a.b.*"), 17): {
            Reference('ROOT'): EntityValue.from_value(frozenset({'test', 3})),
            Reference('a'): EntityValue.from_value({'test'}),
            Reference('a.b'): EntityValue(),
            Reference('a.b.*'): EntityValue.from_value({1}),
            Reference('a.b.c'): EntityValue(value=frozenset()),
            Reference('a.b.c.*'): EntityValue(value=frozenset({1})),
            Reference('a.b.d'): EntityValue(value=frozenset()),
            Reference('a.b.d.*'): EntityValue(value=frozenset({1})),
            Reference('a.b.e'): EntityValue(value=frozenset()),
            Reference('a.b.e.*'): EntityValue(value=frozenset({1})),
            Reference('a.b.f'): EntityValue(value=frozenset()),
            Reference('a.b.f.*'): EntityValue(value=frozenset({1}))
        },
        (Reference("test"), frozenset()): {
            Reference('ROOT'): EntityValue.from_value(frozenset({1, 2, 'test', 'value'})),
            Reference("test.final"): EntityValue(),
            Reference("test.*"): EntityValue.from_value({1}),
            Reference("test.temporary"): EntityValue(),
            Reference('test'): EntityValue(value=frozenset()),
            Reference('test.*'): EntityValue(value=frozenset({1})),
            Reference('test.final'): EntityValue(value=frozenset()),
            Reference('test.final.*'): EntityValue(value=frozenset({1})),
            Reference('test.temporary'): EntityValue(value=frozenset()),
            Reference('test.temporary.*'): EntityValue(value=frozenset({1}))
        },
    }

    for (ref, change), expected_change in expectations.items():
        tree = tree_from_dict(input_dict)
        original_dict = tree_to_dict(tree)
        expected_dict = original_dict | expected_change
        new_value = EntityValue.from_value(change)
        changes = change_node(tree, ref, new_value)
        assert changes == expected_change, f"{ref} -> {change}"
        actual_dict = tree_to_dict(tree)
        assert actual_dict == expected_dict




def test_conflict_resolution_chain():
    def generate_conflict_dict(keys: set[str]) -> Dict[Reference, EntityValue]:
        return {key: EntityValue.from_value(1) for key in keys}

    a = RuleInterpretation(RuleInterpretationState.APPLICABLE, generate_conflict_dict({'a', 'b', 'c'}), 'a->b-c')
    b = RuleInterpretation(RuleInterpretationState.APPLICABLE, generate_conflict_dict({'c', 'd', 'e'}), 'c->d->e')
    c = RuleInterpretation(RuleInterpretationState.APPLICABLE, generate_conflict_dict({'e', 'f', 'g'}), 'e->f->g')
    d = RuleInterpretation(RuleInterpretationState.APPLICABLE, generate_conflict_dict({'h', 'i',    }), 'h->i')
    e = RuleInterpretation(RuleInterpretationState.APPLICABLE, generate_conflict_dict({'a', 'c', 'e'}), 'a->c->e')

    rng = Random()
    rng.seed(1)


    interpretations = frozenset({a, b, c, d, e})

    def resolver(conflicts: List[RuleConflict]) -> FrozenSet[RuleInterpretation]:
        return resolve_conflicts(conflicts, rng)

    test_conflicts = identify_conflicts(interpretations)

    expectations = {
        fs(a, c, d): 2,
        fs(b, d): 1,
        fs(e, d): 1,
    }
    normalized_expectations = {k: v / sum(expectations.values()) for k, v in expectations.items()}

    tracker = get_resolutions(test_conflicts, 1000, resolver)

    normalized_actual = normalize_tracker(tracker)

    diff = diff_trackers(normalized_actual, normalized_expectations)

    for k, v in diff.items():
        assert abs(v) < 0.05, f"{k} -> {v}"