
import dataclasses
from enum import Enum
from typing import List, Tuple, Set, Optional, FrozenSet, Dict, Union

from networkx import MultiDiGraph

from mpl.Parser.ExpressionParsers.machine_expression_parser import MachineFile
from mpl.Parser.ExpressionParsers.reference_expression_parser import ReferenceExpression, Reference, Ref
from mpl.Parser.ExpressionParsers.rule_expression_parser import RuleExpression
from mpl.interpreter.expression_evaluation.engine_context import EngineContext


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


def construct_graph_from_expressions(expressions: FrozenSet[RuleExpression | ReferenceExpression]) -> MultiDiGraph:
    edges: Set[Tuple[Reference, Relationship, Reference|str]] = set()

    for expression in expressions:

        parent: Optional[Reference] = expression.parent and expression.parent.reference.without_types
        match expression:
            case ReferenceExpression() as refx:
                typeless_ref: Reference = expression.reference.without_types
                for type in refx.types:
                    edges.add((typeless_ref, Relationship.IS_A, type))
                if not typeless_ref.is_void:
                    edges.add((typeless_ref, Relationship.DEFINED_IN, parent or 'engine root'))
            case RuleExpression() as rulex:
                edges.add((rulex, Relationship.IS_A, 'rule'))
                edges.add((rulex, Relationship.RUNS_IN, parent or 'engine root'))
                for ref_x in rulex.reference_expressions:
                    this_ref = ref_x.reference
                    if this_ref.is_void:
                        this_ref = this_ref.parent
                    edges.add((rulex, Relationship.USES, this_ref.without_types))
                    for type in this_ref.types or ():
                        edges.add((this_ref.without_types, Relationship.IS_A, type))

    graph = MultiDiGraph()
    for edge in edges:
        graph.add_edge(edge[0], edge[2], relationship=edge[1])

    return graph


def machine_file_context_to_engine_context(context: Dict[ReferenceExpression, FrozenSet]) -> EngineContext:
    from mpl.interpreter.expression_evaluation.entity_value import EntityValue

    result = EngineContext()
    for ref_x, value in context.items():
        ref = ref_x.reference
        result, _ = result.add(ref, EntityValue(value))
    return result


def get_refs_missing_relationship(G: MultiDiGraph, relationship: Relationship) -> Set[Reference]:
    edges = G.edges(data='relationship')
    filtered = filter(lambda edge: edge[2] == relationship, edges)
    not_applicable = set(map(lambda edge: edge[0], filtered))
    refs = filter(lambda ref: isinstance(ref, Reference) and ref not in not_applicable, G.nodes())
    return set(refs)


def assign_missing_types(G: MultiDiGraph) -> MultiDiGraph:
    refs = get_refs_missing_relationship(G, Relationship.IS_A)
    for ref in refs:
        G.add_edge(ref, 'state', relationship=Relationship.IS_A)
    return G


def assign_missing_parents(G: MultiDiGraph) -> MultiDiGraph:
    while True:
        refs = get_refs_missing_relationship(G, Relationship.DEFINED_IN)
        if not refs:
            return G
        for ref in refs:
            expr = ref.to_reference_expression()
            expected_parent_path = expr.path[:-1]
            expected_parent = ReferenceExpression(expected_parent_path).reference
            if not expected_parent.name:
                expected_parent = Ref('ROOT')
            G.add_edge(ref, expected_parent, relationship=Relationship.DEFINED_IN)


def process_machine_file(file: MachineFile) -> (EngineContext, MultiDiGraph, Set):
    with_parentage = assign_parentage_from_machine_file(file)
    graph = construct_graph_from_expressions(with_parentage)
    graph = assign_missing_parents(graph)
    graph = assign_missing_types(graph)

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


def get_reference_types(graph: MultiDiGraph, ref: Reference) -> FrozenSet[str]:
    if ref not in graph.nodes:
        return frozenset()
    out_edges = list(graph.out_edges(ref, data='relationship'))
    return frozenset([x[1] for x in out_edges if x[2] == Relationship.IS_A])


def get_parent_references(G: MultiDiGraph, ref: Reference) -> List[Reference]:
    out_edges = list(G.out_edges(ref, data='relationship'))
    return [x[1] for x in out_edges if x[2] == Relationship.DEFINED_IN]


def get_child_references(G: MultiDiGraph, ref: Reference) -> List[Reference]:
    in_edges = list(G.in_edges(ref, data='relationship'))
    return [x[0] for x in in_edges if x[2] == Relationship.DEFINED_IN]


def get_unqualified_typed_ref(G: MultiDiGraph, ref: Reference) -> ReferenceExpression:
    types = get_reference_types(G, ref)
    my_ref_expr = reference_expression_from_ref(ref, G)
    parent_ref = get_parent_references(G, ref)[0]
    parent_ref_expr = reference_expression_from_ref(parent_ref, G) if parent_ref != 'engine root' else None
    unqualified_ref_expr = unqualify_reference_expression(my_ref_expr, parent_ref_expr)
    return dataclasses.replace(unqualified_ref_expr, types=types, parent=None)


TreeNode = Tuple[ReferenceExpression, List[Union['TreeNode', RuleExpression]]]


def get_child_rules(ref: ReferenceExpression, G: MultiDiGraph) -> List[RuleExpression]:
    result = []

    for child, _, relationship in G.in_edges(ref.reference.without_types, data='relationship'):
        if relationship != Relationship.RUNS_IN:
            continue
        result.append(child)
    return result


def get_child_rules_and_references(ref: ReferenceExpression, graph: MultiDiGraph) -> List[TreeNode | RuleExpression]:
    child_refences = get_child_references(graph, ref.reference)
    results = []
    for child_ref in child_refences:
        child_ref_expr = child_ref.to_reference_expression()
        children = get_child_rules_and_references(child_ref_expr, graph)
        out_child_ref = get_unqualified_typed_ref(graph, child_ref)
        results.append((out_child_ref.reference, children))
    results = sorted(results, key=lambda x: x[0].name)
    child_rules = get_child_rules(ref, graph)
    unqualified_rules = [x.unqualify(ref.path) for x in child_rules]
    return results + sorted(unqualified_rules, key=str)


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
            case Reference() as ref, list() as children if not ref.is_void:
                result += f'{indent}{ref}\n'
                result += entity_tree_to_string(children, depth + 4)
            case ReferenceExpression() as ref, list() as children:
                result += f'{indent}{ref}\n'
                result += entity_tree_to_string(children, depth + 4)
    return result


def engine_to_string(engine: 'MPLEngine') -> str:
    entity_tree = get_entity_tree_from_graph(engine.graph)
    result = entity_tree_to_string(entity_tree)
    if engine.active:
        result += f"\n---\n{engine.context}\n"

    return result


def get_sibling_groups(graph: MultiDiGraph) -> Dict[Reference, Set[Reference]]:
    refs = {x for x in graph.nodes() if isinstance(x, Reference) and not x.is_void}
    result = dict()
    for ref in refs:
        parent = get_parent_references(graph, ref)[0]
        siblings = get_child_references(graph, parent)
        result[ref] = set(siblings)
    return result


def get_type_map(graph: MultiDiGraph) -> Dict[Reference, FrozenSet[str]]:
    refs = {x for x in graph.nodes() if isinstance(x, Reference) and not x.is_void}
    result: Dict[Reference, FrozenSet[str]] = dict()
    for ref in refs:
        types = get_reference_types(graph, ref)
        result[ref] = types
    return result


def get_parent_map(g: MultiDiGraph) -> Dict[Reference, Reference]:
    refs = {x for x in g.nodes() if isinstance(x, Reference) and not x.is_void}
    result = dict()
    for ref in refs:
        parents = get_parent_references(g, ref)
        if parents:
            result[ref] = parents[0]
        else:
            result[ref] = None
    return result


def get_child_map(graph: MultiDiGraph) -> Dict[Reference, Set[Reference]]:
    refs = {x for x in graph.nodes() if isinstance(x, Reference) and not x.is_void}
    result = dict()
    for ref in refs:
        children = set(get_child_references(graph, ref))
        result[ref] = children - {ref.void}

    return result


def get_all_descendants(graph: MultiDiGraph, ref: Reference) -> Set[Reference]:
    result = set()
    for child in get_child_references(graph, ref):
        result.add(child)
        result |= get_all_descendants(graph, child)
    return result


def get_descendant_map(graph: MultiDiGraph) -> Dict[Reference, Set[Reference]]:
    refs = {x for x in graph.nodes() if isinstance(x, Reference) and not x.is_void}
    result = dict()
    for ref in refs:
        result[ref] = get_all_descendants(graph, ref)
    return result
