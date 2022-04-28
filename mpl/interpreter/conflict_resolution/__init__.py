import dataclasses
import random
from enum import Enum, auto

from typing import List, Set, FrozenSet, Dict, Tuple, Union

import networkx as nx

from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference
from mpl.interpreter.expression_evaluation.entity_value import EntityValue
from mpl.interpreter.rule_evaluation import RuleInterpretation, RuleInterpretationState


def compress_conflict_list(query_conflicts: List[Set[RuleInterpretation]]) -> List[Set[RuleInterpretation]]:
    i = 0
    while i < len(query_conflicts):
        concurrent_conflict = query_conflicts[i]
        next_index = i + 1
        while next_index < len(query_conflicts):
            next_conflict = query_conflicts[next_index]
            if next_conflict.issubset(concurrent_conflict):
                query_conflicts.pop(next_index)
            else:
                next_index += 1
        i += 1
    return query_conflicts


@dataclasses.dataclass(frozen=True, order=True)
class RuleConflict:
    target_interpretation: RuleInterpretation
    conflicting_interpretations: FrozenSet[RuleInterpretation]


@dataclasses.dataclass(frozen=True, order=True)
class InterpretationChoices:
    Accepted: FrozenSet[RuleInterpretation] = frozenset()
    Rejected: FrozenSet[RuleInterpretation] = frozenset()


def construct_change_graph(interpretations: FrozenSet[RuleInterpretation]) \
        -> Tuple[nx.DiGraph, Dict[int, RuleInterpretation]]:
    graph = nx.DiGraph()

    interp_index = dict()

    for interp in interpretations:
        if interp.state == RuleInterpretationState.NOT_APPLICABLE:
            continue
        interp_key = hash(interp)
        interp_index[interp_key] = interp
        for changed_key in interp.keys:
            graph.add_edge(interp_key, changed_key)

    return graph, interp_index


def drop_non_competitive_interpretations(target: RuleInterpretation, candidates: FrozenSet[RuleInterpretation]) \
        -> FrozenSet[RuleInterpretation]:
    result = set()
    for candidate in candidates:
        if candidate.state == RuleInterpretationState.NOT_APPLICABLE:
            continue
        for change in candidate.changes:
            if change not in target.changes:
                continue
            if target.changes[change] == candidate.changes[change]:
                continue
            result.add(candidate)

    return frozenset(result)


class InterpretationRequirementType(Enum):
    DONT_CHANGE = auto()
    VOID = auto()


def generate_interpretation_requirements(target: RuleInterpretation) \
        -> Dict[Reference, Union['EntityValue', InterpretationRequirementType]]:
    result = {}
    for k, _ in target.changes.items():
        result[k] = 'ADJUST'

    return result | target.core_state_assertions


def detect_conflict(target: RuleInterpretation, candidate: RuleInterpretation) -> FrozenSet[Reference]:
    if not target.state == candidate.state == RuleInterpretationState.APPLICABLE:
        return frozenset()

    target_requirements = generate_interpretation_requirements(target)
    candidate_requirements = generate_interpretation_requirements(candidate)

    result = set()

    for k, v in target_requirements.items():
        other_v = candidate_requirements.get(k, None)
        match v, other_v:
            case 'TARGET' | 'CONSUME', None:
                continue
            case 'TARGET' | 'CONSUME', y:
                result.add(k)
            case x, 'TARGET' | 'CONSUME':
                result.add(k)

    return frozenset(result)


def construct_conflict_map(change_graph: nx.DiGraph, interp_index: Dict[int, RuleInterpretation]) \
        -> Dict[RuleInterpretation, FrozenSet[RuleInterpretation]]:
    result = {}

    for k, interp in interp_index.items():
        if interp.state == RuleInterpretationState.NOT_APPLICABLE:
            continue

        changed_keys = interp.keys
        other_interps = set()
        for key in changed_keys:
            tmp = set(change_graph.predecessors(key))
            other_interps |= tmp

        conflicts = set()

        for node in other_interps:
            other_interp = interp_index[node]
            if other_interp.state == RuleInterpretationState.NOT_APPLICABLE:
                continue
            if other_interp == interp:
                continue
            conflict_keys = detect_conflict(interp, other_interp)
            if conflict_keys:
                conflicts.add(other_interp)

        result[interp] = frozenset(conflicts)

    return result


def identify_conflicts(interpretations: FrozenSet[RuleInterpretation]) \
        -> Dict[RuleInterpretation, FrozenSet[RuleInterpretation]]:

    tmp_graph, interp_index = construct_change_graph(interpretations)
    result = construct_conflict_map(tmp_graph, interp_index)

    return result


def choose_outcome(
        target: RuleInterpretation,
        conflict_map: Dict[RuleInterpretation, FrozenSet[RuleInterpretation]],
        existing_choices: InterpretationChoices) -> InterpretationChoices:

    if target in existing_choices.Rejected:
        return existing_choices

    conflicting_interpretations = conflict_map[target]

    if target in existing_choices.Accepted:
        new_rejections = existing_choices.Rejected | conflicting_interpretations
        return dataclasses.replace(existing_choices, Rejected=new_rejections)

    remaining_conflicts = conflicting_interpretations - existing_choices.Rejected
    if remaining_conflicts & existing_choices.Accepted:
        new_rejections = existing_choices.Rejected | {target}
        return dataclasses.replace(existing_choices, Rejected=new_rejections)

    if not remaining_conflicts:
        new_acceptance = existing_choices.Accepted | {target}
        return dataclasses.replace(existing_choices, Accepted=new_acceptance)

    rc_list = list(remaining_conflicts)
    rc_weights = [x.scenario_weight for x in rc_list] or [0]

    candidates = [target] + rc_list

    weights = [target.scenario_weight] + rc_weights

    #protection from zeroes
    if weights == [weights[0]] * len(weights):
        weights = [1] * len(weights)

    choice = random.choices(candidates, weights=weights, k=1)[0]

    new_acceptance = existing_choices.Accepted | {choice}
    new_rejections = existing_choices.Rejected | conflict_map[choice]

    result = dataclasses.replace(existing_choices, Accepted=new_acceptance, Rejected=new_rejections)
    return result


def resolve_conflict_map(
        conflict_map: Dict[RuleInterpretation, FrozenSet[RuleInterpretation]]) -> FrozenSet[RuleInterpretation]:
    out = InterpretationChoices()
    sorted_keys = sorted(conflict_map.keys(), key=lambda x: len(conflict_map[x]))
    for k in sorted_keys:
        out = choose_outcome(k, conflict_map, out)
    return out.Accepted


def compress_interpretations(interpretations: FrozenSet[RuleInterpretation]) \
        -> Dict[Reference, 'EntityValue']:
    result = {}
    for interp in interpretations:
        result |= interp.changes
    return result


def get_resolutions(conflicts: Dict[RuleInterpretation, FrozenSet[RuleInterpretation]], trials):
    from collections import defaultdict
    resolution_tracker = defaultdict(lambda: 0)
    random.seed(0)
    for x in range(trials):
        resolved = resolve_conflict_map(conflicts)
        resolution_tracker[resolved] += 1
        resolution_tracker['total'] += 1

    return resolution_tracker


def normalize_tracker(tracker):
    total = 0
    if 'total' in tracker:
        total = tracker['total']
        del tracker['total']
    else:
        total = sum(tracker.values())
    return {k: v / total for k, v in tracker.items()}
