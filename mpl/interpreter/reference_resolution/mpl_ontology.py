
import dataclasses
from enum import Enum
from random import random, Random
from typing import List, Tuple, Set, Optional, FrozenSet, Dict, Union

import networkx as nx
from networkx import MultiDiGraph

from mpl.Parser.ExpressionParsers.machine_expression_parser import MachineFile
from mpl.Parser.ExpressionParsers.reference_expression_parser import ReferenceExpression, Reference, Ref
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

        parent: Optional[Reference] = expression.parent and expression.parent.reference.without_types
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


def machine_file_context_to_engine_context(context: Dict[ReferenceExpression, FrozenSet]) -> EngineContext:
    result = EngineContext()
    for ref_x, value in context.items():
        ref = ref_x.reference
        result[ref.without_types] = MPLEntity(ref.name, value)
    return result


def process_machine_file(file: MachineFile) -> (EngineContext, MultiDiGraph):
    with_parentage = assign_parentage_from_machine_file(file)
    graph = construct_graph_from_expressions(with_parentage)
    result_context = EngineContext.from_graph(graph)
    if file.context:
        loaded_context = machine_file_context_to_engine_context(file.context)
        result_context = result_context | loaded_context
    return result_context, graph


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


def reference_expression_from_ref(ref: Reference, G:MultiDiGraph) -> ReferenceExpression:

    types = get_reference_types(G, ref)

    expr = ref.to_reference_expression()
    expr = dataclasses.replace(expr, types=types)
    return expr


def unqualify_reference_expression(expr: ReferenceExpression, parent:ReferenceExpression) -> ReferenceExpression:
    if not parent:
        return expr
    parent_path_length = len(parent.path)
    new_path = expr.path[parent_path_length:]
    return dataclasses.replace(expr, path=new_path, parent=parent)


def get_reference_types(G: MultiDiGraph, ref: Reference) -> FrozenSet[str]:
    if ref not in G.nodes:
        return frozenset()
    out_edges = list(G.out_edges(ref, data='relationship'))
    return frozenset([x[1] for x in out_edges if x[2] == Relationship.IS_A])


def get_parent_references(G: MultiDiGraph, ref: Reference) -> List[Reference]:
    out_edges = list(G.out_edges(ref, data='relationship'))
    return [x[1] for x in out_edges if x[2] == Relationship.DEFINED_IN]


def get_unqualified_typed_ref(G: MultiDiGraph, ref: Reference) -> ReferenceExpression:
    types = get_reference_types(G, ref)
    my_ref_expr = reference_expression_from_ref(ref, G)
    parent_ref = get_parent_references(G, ref)[0]
    parent_ref_expr = reference_expression_from_ref(parent_ref, G) if parent_ref != 'engine root' else None
    unqualified_ref_expr = unqualify_reference_expression(my_ref_expr, parent_ref_expr)
    return dataclasses.replace(unqualified_ref_expr, types=types, parent=None)


TreeNode = Tuple[ReferenceExpression, List[Union['TreeNode', RuleExpression]]]


def get_child_references(ref: ReferenceExpression, G: MultiDiGraph) -> List[Reference]:
    result = []

    for child_ref, _, relationship in G.in_edges(ref.reference.without_types, data='relationship'):
        if relationship != Relationship.DEFINED_IN:
            continue
        result.append(child_ref)

    return result


def get_child_rules(ref: ReferenceExpression, G: MultiDiGraph) -> List[RuleExpression]:
    result = []

    for child, _, relationship in G.in_edges(ref.reference.without_types, data='relationship'):
        if relationship != Relationship.RUNS_IN:
            continue
        result.append(child)
    return result


def get_child_rules_and_references(ref: ReferenceExpression, G: MultiDiGraph) -> List[TreeNode | RuleExpression]:
    child_refences = get_child_references(ref, G)
    results = []
    for child_ref in child_refences:
        child_ref_expr = child_ref.to_reference_expression()
        children = get_child_rules_and_references(child_ref_expr, G)
        out_child_ref = get_unqualified_typed_ref(G, child_ref)
        results.append((out_child_ref.reference, children))
    results = sorted(results, key=lambda x: x[0].name)
    child_rules = get_child_rules(ref, G)
    unqualified_rules = [x.unqualify(ref.path) for x in child_rules]
    return results + sorted(unqualified_rules, key=str)

    return results + unqualified_rules


def get_entity_tree_from_graph(G: MultiDiGraph) -> List[TreeNode]:
    root_edges = list(G.in_edges('engine root', data='relationship'))
    result = []
    refs = [x[0] for x in root_edges if isinstance(x[0], Reference)]
    rules = [x[0] for x in root_edges if isinstance(x[0], RuleExpression)]

    for ref in refs:
        expr = ref.to_reference_expression()
        children = get_child_rules_and_references(expr, G)
        out_ref = get_unqualified_typed_ref(G, ref)
        result.append((out_ref, children))

    return result + sorted(rules, key=str)


def entity_tree_to_string(tree: List[TreeNode | RuleExpression], depth: int = 0) -> str:
    result = ''
    indent = ' ' * depth
    for node in tree:
        match node:
            case RuleExpression():
                result += f'{indent}{node}\n'
            case ReferenceExpression() | Reference() as ref_x, list() as children:
                result += f'{indent}{ref_x}\n'
                result += entity_tree_to_string(children, depth + 4)
    return result


def engine_to_string(engine: 'MPLEngine') -> str:
    entity_tree = get_entity_tree_from_graph(engine.graph)
    result = entity_tree_to_string(entity_tree)
    if engine.active:
        result += f"\n---\n{engine.context}\n"

    return result

