import dataclasses
import random

from typing import List, Set, FrozenSet, Dict

import networkx as nx

from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference
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


def identify_conflicts(interpretations: FrozenSet[RuleInterpretation]) \
        -> Dict[RuleInterpretation, FrozenSet[RuleInterpretation]]:
    affected_keys = set()
    interp_index = dict()

    tmp_graph = nx.DiGraph()

    for interp in interpretations:
        if interp.state == RuleInterpretationState.NOT_APPLICABLE:
            continue
        affected_keys |= interp.changes.keys()
        interp_key = hash(interp)
        interp_index[interp_key] = interp
        for changed_key in interp.keys:
            tmp_graph.add_edge(interp_key, changed_key)

    out = {}

    for interp in interpretations:
        if interp.state == RuleInterpretationState.NOT_APPLICABLE:
            continue

        changed_keys = interp.keys
        changed_key_nodes = tmp_graph.nbunch_iter(changed_keys)
        changed_by = set()
        for node in changed_key_nodes:
            tmp = set(tmp_graph.predecessors(node))
            changed_by |= tmp

        result = changed_by - {hash(interp)}
        result = {interp_index[x] for x in result}
        out[interp] = frozenset(result)

    return out


def choose_outcome(
        target: RuleInterpretation,
        conflict_map: Dict[RuleInterpretation, FrozenSet[RuleInterpretation]],
        existing_choices: InterpretationChoices,
        seed) -> InterpretationChoices:

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
    rc_weights = [x.scenario_weight for x in rc_list]

    candidates = [target] + rc_list
    weights = [target.scenario_weight] + rc_weights
    # random.seed(seed)
    choice = random.choices(candidates, weights=weights, k=1)[0]

    new_acceptance = existing_choices.Accepted | {choice}
    new_rejections = existing_choices.Rejected | conflict_map[choice]

    result = dataclasses.replace(existing_choices, Accepted=new_acceptance, Rejected=new_rejections)
    return result


def resolve_conflict_map(
        conflict_map: Dict[RuleInterpretation, FrozenSet[RuleInterpretation]],
        seed) -> FrozenSet[RuleInterpretation]:
    out = InterpretationChoices()
    sorted_keys = sorted(conflict_map.keys(), key=lambda x: len(conflict_map[x]))
    for k in sorted_keys:
        out = choose_outcome(k, conflict_map, out, seed)
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
        resolved = resolve_conflict_map(conflicts, x)
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
