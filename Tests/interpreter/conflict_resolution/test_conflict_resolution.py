import dataclasses
import random
from collections import defaultdict

from Tests import quick_parse
from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference
from mpl.Parser.ExpressionParsers.rule_expression_parser import RuleExpression
from mpl.interpreter.conflict_resolution import compress_conflict_list, identify_conflicts, resolve_conflicts, \
    RuleConflict
from mpl.interpreter.reference_resolution.reference_graph_resolution import MPLEntity, MPLEntityClass
from mpl.interpreter.rule_evaluation import create_rule_interpreter
from mpl.lib import fs


def get_resolutions(conflicts, trials):
    resolution_tracker = defaultdict(lambda: 0)

    for x in range(trials):
        resolved = resolve_conflicts(conflicts)
        resolution_tracker[resolved] += 1
        resolution_tracker['total'] += 1

    return resolution_tracker


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
    In = dict()
    for rule_input in rule_inputs:
        expression = quick_parse(RuleExpression, rule_input)
        interpreter = create_rule_interpreter(expression)
        interpreter = dataclasses.replace(interpreter, name=rule_input)
        interpretation = interpreter.interpret(context)
        interpretations.append(interpretation)
        In[rule_input] = interpretation
    return interpretations, In


full_context = {
    Reference('A'): MPLEntity(1, 'A', MPLEntityClass.STATE, fs(1)),
    Reference('B'): MPLEntity(1, 'B', MPLEntityClass.STATE, fs(2)),
    Reference('C'): MPLEntity(1, 'C', MPLEntityClass.STATE, fs(3)),
    Reference('D'): MPLEntity(1, 'D', MPLEntityClass.STATE, fs(4)),
    Reference('One'): MPLEntity(1, 'One', MPLEntityClass.STATE, fs(5)),
    Reference('Two'): MPLEntity(1, 'Two', MPLEntityClass.STATE, fs(6)),
    Reference('Three'): MPLEntity(1, 'Three', MPLEntityClass.STATE, fs(7)),
    Reference('Four'): MPLEntity(1, 'Four', MPLEntityClass.STATE, fs(8)),
    Reference('Five'): MPLEntity(1, 'Five', MPLEntityClass.STATE, fs(9)),
    Reference('Six'): MPLEntity(1, 'Six', MPLEntityClass.STATE, fs(10)),
    Reference('Seven'): MPLEntity(1, 'Seven', MPLEntityClass.STATE, fs(11)),
}

"""
Turn Start -> Turn Action
!Turn Action ~> Turn End

Turn Start ~> Move

Turn Action -> %{believed attack damage} -> Attack
Turn Action -> extern(calculate_move_value) -> Double Move
Turn Action -> %{spell damage} -> Spell

"""



def test_conflict_resolution_simple_conflict():

    A = 'One -> Two'
    B = 'Two & Three -> Four'
    C = 'Four -> Five'
    D = 'Six -> Seven'
    E = 'One -> Three -> Five'

    rule_inputs = [A, B, C, D, E]

    interpretations, In = get_interpretations(rule_inputs, full_context)

    conflicts = identify_conflicts(interpretations)

    random.seed(0)

    trials = 10000

    resolution_tracker = get_resolutions(conflicts, trials)

    outcome_1 = frozenset({In[A], In[C], In[D]})
    outcome_2 = frozenset({In[B], In[D]})
    outcome_3 = frozenset({In[E], In[D]})

    expected_outcomes = {
        outcome_1: 2,
        outcome_2: 1,
        outcome_3: 1,
    }

    assert_results_in_bounds(resolution_tracker, expected_outcomes)


def test_conflict_resolution_sequential_conflict():
    A = 'One -> Two -> Three'
    B = 'Three -> Four -> Five'
    C = 'Five -> Six'
    D = 'A -> B'

    rule_inputs = [A, B, C, D]

    interpretations, In = get_interpretations(rule_inputs, full_context)

    conflicts = identify_conflicts(interpretations)

    trials = 10000

    resolution_tracker = get_resolutions(conflicts, trials)

    outcome_1 = frozenset({In[A], In[C], In[D]})
    outcome_2 = frozenset({In[B], In[D]})

    expected_outcomes = {
        outcome_1: 2,
        outcome_2: 1,
    }

    assert_results_in_bounds(resolution_tracker, expected_outcomes)




# TODO: test to make sure unequal distributions are handled correctly

