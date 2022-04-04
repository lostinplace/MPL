import dataclasses
import random
from collections import defaultdict
from typing import List, FrozenSet, Dict, Callable

from Tests import quick_parse
from Tests.interpreter.expression_evaluation.test_context_tree_interpretation import diff_trackers
from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference
from mpl.Parser.ExpressionParsers.rule_expression_parser import RuleExpression
from mpl.interpreter.conflict_resolution import identify_conflicts, normalize_tracker, get_resolutions, \
    resolve_conflict_map
from mpl.interpreter.expression_evaluation.engine_context import EngineContext

from mpl.interpreter.rule_evaluation import create_rule_interpreter, RuleInterpretation, RuleInterpretationState
from mpl.lib import fs
from mpl.interpreter.expression_evaluation.entity_value import EntityValue
from mpl.lib.context_tree.context_tree_implementation import ContextTree


def assert_results_in_bounds(tracker: dict, expected_outcomes: dict):
    total = tracker['total']
    sum_of_expected = sum(expected_outcomes.values())
    baseline = total / sum_of_expected
    for outcome in expected_outcomes:
        outcome_count = tracker[outcome]
        assert outcome_count > 0
        assert outcome_count >= expected_outcomes[outcome] * baseline * 0.95
        assert outcome_count <= expected_outcomes[outcome] * baseline * 1.05


def get_interpretations(rule_inputs, context):
    interpretations = []
    result = dict()
    for rule_input in rule_inputs:
        expression = quick_parse(RuleExpression, rule_input)
        interpreter = create_rule_interpreter(expression)
        interpreter = dataclasses.replace(interpreter, name=rule_input)
        interpretation = interpreter.interpret(context)
        interpretations.append(interpretation)
        result[rule_input] = interpretation
    return frozenset(interpretations), result


fc = {
    Reference('A'): EntityValue(fs(1)),
    Reference('B'): EntityValue(fs(2)),
    Reference('C'): EntityValue(fs(3)),
    Reference('D'): EntityValue(fs(4)),
    Reference('One'): EntityValue(fs(5)),
    Reference('Two'): EntityValue(fs(6)),
    Reference('Three'): EntityValue(fs(7)),
    Reference('Four'): EntityValue(fs(8)),
    Reference('Five'): EntityValue(fs(9)),
    Reference('Six'): EntityValue(fs(10)),
    Reference('Seven'): EntityValue(fs(11)),
    Reference('Eight'): EntityValue(fs(8)),
    Reference('Nine'): EntityValue(fs(9)),
    Reference('Ten'): EntityValue(fs(10)),
}

full_context = EngineContext(ContextTree.from_dict(fc))



"""
Turn Start -> Turn Action
!Turn Action ~> Turn End

Turn Start ~> Move

Turn Action -> %{believed attack damage} -> Attack
Turn Action -> extern(calculate_move_value) -> Double Move
Turn Action -> %{spell damage} -> Spell

"""


def test_conflict_resolution_simple_conflict():

    a = 'One -> Two'
    b = 'Two & Three -> Four'
    c = 'Four -> Five'
    d = 'Six -> Seven'
    e = 'One -> Three -> Five'

    random.seed(1)
    rule_inputs = [a, b, c, d, e]

    interpretations, tmp = get_interpretations(rule_inputs, full_context)

    conflicts = identify_conflicts(interpretations)

    outcome_1 = frozenset({tmp[a], tmp[c], tmp[d]})
    outcome_2 = frozenset({tmp[b], tmp[d]})
    outcome_3 = frozenset({tmp[e], tmp[d]})

    expected_outcomes = {
        outcome_1: 1,
        outcome_2: 1,
        outcome_3: 1,
    }

    normalized_expectations = normalize_tracker(expected_outcomes)

    trials = 10000
    resolution_tracker = get_resolutions(conflicts, trials)

    normalized_actual = normalize_tracker(resolution_tracker)

    diff = diff_trackers(normalized_expectations, normalized_actual)

    for k, v in diff.items():
        assert abs(v) < 0.05, f"{k} -> {v}"


def test_conflict_resolution_sequential_conflict():
    a = 'One -> Two -> Three'
    b = 'Three -> Four -> Five'
    c = 'Five -> Six'
    d = 'A -> B'

    rule_inputs = [a, b, c, d]

    interpretations, tmp = get_interpretations(rule_inputs, full_context)

    expected_outcomes = {
        frozenset({tmp[a], tmp[c], tmp[d]}): 1,
        frozenset({tmp[b], tmp[d]}): 1,
    }

    normalized_expectations = normalize_tracker(expected_outcomes)

    conflicts = identify_conflicts(interpretations)

    trials = 10000

    resolution_tracker = get_resolutions(conflicts, trials)

    normalized_actual = normalize_tracker(resolution_tracker)

    diff = diff_trackers(normalized_actual, normalized_expectations)

    for k, v in diff.items():
        assert abs(v) < 0.05, f"{k} -> {v}"


def test_conflict_resolution_doesnt_break():

    rule_inputs = [
        'One -> Two',
        'Two & Three -> Four',
        'Four -> Five',
        'Six -> Seven',
        'One -> Three -> Five',
        'Four -> Eight',
        'Eight -> Nine',
        'Nine -> Ten',
        'Ten -> Four',
        'Nine -> Five',
        'Nine & One -> One',
    ]

    interpretations, tmp = get_interpretations(rule_inputs, full_context)

    random.seed(1)

    conflicts = identify_conflicts(interpretations)
    for i in range(5000):
        actual = resolve_conflict_map(conflicts, i)
        affected_keys = set()
        for c in actual:
            intersection = affected_keys & c.keys
            assert not intersection, f"conflict on keys: {intersection}"
            affected_keys |= c.keys
