import dataclasses
import random
from dataclasses import dataclass
from typing import List, Set, FrozenSet, Tuple, Dict

import networkx as nx

from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference
from mpl.interpreter.rule_evaluation import RuleInterpretation
from mpl.lib.query_logic import MPL_Context


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


@dataclass(frozen=True, order=True)
class RuleConflict:
    target_interpretation: RuleInterpretation
    conflicting_interpretations: FrozenSet[RuleInterpretation]


@dataclass(frozen=True, order=True)
class Resolutions:
    Truth: FrozenSet[RuleInterpretation] = frozenset()
    Falsehood: FrozenSet[RuleInterpretation] = frozenset()


def identify_conflicts(interpretations: List[RuleInterpretation]) -> List[RuleConflict]:
    affected_keys = set()
    interp_index = dict()

    G = nx.DiGraph()

    for interp in interpretations:
        affected_keys |= interp.changes.keys()
        interp_key = hash(interp)
        interp_index[interp_key] = interp
        for changed_key in interp.changes:
            G.add_edge(interp_key, changed_key)

    out = list()

    for interp in interpretations:

        changed_keys = interp.changes.keys()
        changed_key_nodes = G.nbunch_iter(changed_keys)
        changed_by = set()
        for node in changed_key_nodes:
            tmp = set(G.predecessors(node))
            changed_by |= tmp

        result = changed_by - {hash(interp)}
        result = {interp_index[x] for x in result}
        tmp = RuleConflict(interp, frozenset(result))
        out.append(tmp)

    out = sorted(out, key=lambda x: len(x.conflicting_interpretations), reverse=True)
    return out


def resolve_conflict(
        conflict: RuleConflict,
        resolutions: Resolutions = Resolutions()
) -> Resolutions:

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
    resolution = random.choices(choices, weights=weights, k=1)[0]
    match resolution:
        case x if x == remaining_conflicts:
            new_falsehood = resolutions.Falsehood | {conflict.target_interpretation}
            return dataclasses.replace(resolutions, Falsehood=new_falsehood)
        case conflict.target_interpretation:
            new_truth = resolutions.Truth | {conflict.target_interpretation}
            return dataclasses.replace(resolutions, Truth=new_truth)


def resolve_conflicts(
        conflicts: List[RuleConflict]
) -> FrozenSet[RuleInterpretation]:
    resolutions = Resolutions()

    for conflict in conflicts:
        resolutions = resolve_conflict(conflict, resolutions)

    return frozenset(resolutions.Truth)