
import dataclasses
from enum import Enum
from typing import List, Tuple, Set, Optional, FrozenSet, Dict

import networkx as nx
from networkx import MultiDiGraph

from mpl.Parser.ExpressionParsers.machine_expression_parser import MachineFile
from mpl.Parser.ExpressionParsers.reference_expression_parser import ReferenceExpression, Reference
from mpl.Parser.ExpressionParsers.rule_expression_parser import RuleExpression
from mpl.interpreter.expression_evaluation.engine_context import EngineContext
from mpl.interpreter.reference_resolution.mpl_entity import MPLEntity


class Relationship(Enum):
    IS_A = "is a"
    RUNS_IN = "runs in"
    USES = "uses"
    DEFINED_IN = "defined in"


@dataclasses.dataclass(frozen=True, order=True)
class PathInfo:
    names: Tuple[str, ...]
    depths: Tuple[int, ...]
    parent_path: Tuple[str, ...] = ()


def get_current_path(
    path: str | Tuple[str, ...],
    depth: int,
    existing_path: PathInfo = None
) -> PathInfo:

    if isinstance(path, str):
        path = (path,)

    new_depths = (depth, ) * len(path)

    if depth == 0 or not existing_path:
        return PathInfo(path, new_depths, ())

    result_path = tuple()
    result_depths = tuple()

    for node, h_depth in zip(existing_path.names, existing_path.depths):
        if h_depth >= depth:
            return PathInfo(result_path + path, result_depths + new_depths, result_path)
        result_path += (node,)
        result_depths += (h_depth,)

    return PathInfo(result_path + path, result_depths + new_depths, result_path)


def assign_parentage_from_machine_file(file: MachineFile) -> FrozenSet[RuleExpression | ReferenceExpression]:
    rule_expressions = set()
    current_path: PathInfo = PathInfo((), ())
    ref_x_cache: Dict[Tuple[str], ReferenceExpression] = {}

    for line in file.lines:
        match line:
            case ReferenceExpression() as refx:
                depth = line.metadata.start
                current_path = get_current_path(refx.path, depth, current_path)
                current_ref_expression = refx.qualify(current_path.parent_path)

                parent: ReferenceExpression = ref_x_cache.get(current_path.parent_path)
                types = current_ref_expression.types or set()
                if parent and 'state' in parent.types:
                    types |= {'state'}

                current_ref_expression = dataclasses.replace(current_ref_expression, parent=parent, types=frozenset(types))

                ref_x_cache[current_ref_expression.path] = current_ref_expression

            case RuleExpression() as rulex:
                depth = line.metadata.start
                current_path = get_current_path((), depth, current_path)
                qualified_rule_expression = rulex.qualify(current_path.parent_path)
                parent = ref_x_cache.get(current_path.parent_path)
                if parent:
                    qualified_rule_expression = dataclasses.replace(qualified_rule_expression, parent = parent)
                rule_expressions.add(qualified_rule_expression)

    result = rule_expressions | set(ref_x_cache.values())
    return frozenset(result)


def construct_graph_from_expressions(expressions: Set[RuleExpression | ReferenceExpression]) -> MultiDiGraph:
    edges: Set[Tuple[Reference, Relationship, Reference|str]] = set()

    for expression in expressions:

        parent:Optional[Reference] = expression.parent and expression.parent.reference.without_types
        match expression:
            case ReferenceExpression() as refx:
                typeless_ref: Reference = expression.reference.without_types
                for type in refx.types:
                    edges.add((typeless_ref, Relationship.IS_A, type))
                edges.add((typeless_ref, Relationship.DEFINED_IN, parent or 'engine root'))
            case RuleExpression() as rulex:
                edges.add((rulex, Relationship.IS_A, 'rule'))
                edges.add((rulex, Relationship.RUNS_IN, parent or 'engine root'))
                for ref_x in rulex.reference_expressions:
                    edges.add((rulex, Relationship.USES, ref_x.reference.without_types))
                    for type in ref_x.types or ():
                        edges.add((ref_x.reference.without_types, Relationship.IS_A, type))

    G = MultiDiGraph()
    for edge in edges:
        G.add_edge(edge[0], edge[2], relationship=edge[1])

    return G


def process_machine_file(file: MachineFile) -> (EngineContext, MultiDiGraph):
    with_parentage = assign_parentage_from_machine_file(file)
    graph = construct_graph_from_expressions(with_parentage)
    return EngineContext.from_graph(graph), graph


def get_edges_by_type(G: MultiDiGraph, types: str|Set[str]) -> List[Tuple[str, str]]:
    if isinstance(types, str):
        types = {types}
    return [(u, v) for u, v, d in G.edges(data=True) if d['type'] in types]


def rule_expressions_from_graph(G: MultiDiGraph) -> FrozenSet[RuleExpression]:
    rule_edges = G.in_edges('rule', data='relationship')
    rule_expressions = set()

    for origin, _, type in rule_edges:
        match origin, type:
            case RuleExpression(), Relationship.IS_A:
                rule_expressions.add(origin)
    return frozenset(rule_expressions)



