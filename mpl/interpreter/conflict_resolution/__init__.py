import dataclasses
import random
from typing import List, Set, FrozenSet, Dict, Optional

import networkx as nx

from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference
from mpl.interpreter.rule_evaluation import RuleInterpretation


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
class Resolutions:
    Truth: FrozenSet[RuleInterpretation] = frozenset()
    Falsehood: FrozenSet[RuleInterpretation] = frozenset()


def identify_conflicts(interpretations: FrozenSet[RuleInterpretation]) -> List[RuleConflict]:
    affected_keys = set()
    interp_index = dict()

    tmp_graph = nx.DiGraph()

    for interp in interpretations:
        affected_keys |= interp.changes.keys()
        interp_key = hash(interp)
        interp_index[interp_key] = interp
        for changed_key in interp.keys:
            tmp_graph.add_edge(interp_key, changed_key)

    out = list()

    for interp in interpretations:

        changed_keys = interp.keys
        changed_key_nodes = tmp_graph.nbunch_iter(changed_keys)
        changed_by = set()
        for node in changed_key_nodes:
            tmp = set(tmp_graph.predecessors(node))
            changed_by |= tmp

        result = changed_by - {hash(interp)}
        result = {interp_index[x] for x in result}
        tmp = RuleConflict(interp, frozenset(result))
        out.append(tmp)

    out = sorted(out, key=lambda x: len(x.conflicting_interpretations), reverse=True)
    return out


def resolve_conflict(
        conflict: RuleConflict,
        resolutions: Resolutions = Resolutions(),
        rng: Optional[random.Random] = None
) -> Resolutions:
    if rng is None:
        rng = random.Random()

    remaining_conflicts = conflict.conflicting_interpretations - resolutions.Falsehood
    if not remaining_conflicts:
        new_truth = resolutions.Truth | {conflict.target_interpretation}
        return dataclasses.replace(resolutions, Truth=new_truth)

    if remaining_conflicts.intersection(resolutions.Truth):
        new_falsehood = resolutions.Falsehood | {conflict.target_interpretation}
        return dataclasses.replace(resolutions, Falsehood=new_falsehood)

    conflict_weight = sum(x.scenario_weight for x in remaining_conflicts)
    this_weight = conflict.target_interpretation.scenario_weight
    choices = [conflict.target_interpretation,  remaining_conflicts]
    weights = [this_weight, conflict_weight]
    resolution = rng.choices(choices, weights=weights, k=1)[0]
    match resolution:
        case x if x == remaining_conflicts:
            new_falsehood = resolutions.Falsehood | {conflict.target_interpretation}
            return dataclasses.replace(resolutions, Falsehood=new_falsehood)
        case conflict.target_interpretation:
            new_truth = resolutions.Truth | {conflict.target_interpretation}
            return dataclasses.replace(resolutions, Truth=new_truth)


def resolve_conflicts(
        conflicts: List[RuleConflict],
        rng: Optional[random.Random] = None
) -> FrozenSet[RuleInterpretation]:
    if rng is None:
        rng = random.Random()

    resolutions = Resolutions()

    for conflict in conflicts:
        resolutions = resolve_conflict(conflict, resolutions, rng)

    return frozenset(resolutions.Truth)


def compress_interpretations(interpretations: FrozenSet[RuleInterpretation]) \
        -> Dict[Reference, FrozenSet[RuleInterpretation]]:
    result = {}
    for interp in interpretations:
        result |= interp.changes
    return result


def get_resolutions(conflicts, trials, conflict_resolver):
    from collections import defaultdict
    resolution_tracker = defaultdict(lambda: 0)

    for x in range(trials):
        resolved = conflict_resolver(conflicts)
        resolution_tracker[resolved] += 1
        resolution_tracker['total'] += 1

    return resolution_tracker


def normalize_tracker(tracker):
    return {k: v / tracker['total'] for k, v in tracker.items()}
