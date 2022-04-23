import dataclasses
from typing import FrozenSet, Dict, Union, Set, Tuple, Optional, Iterator

from networkx import MultiDiGraph
from sympy import Symbol

from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference, Ref
from mpl.interpreter.expression_evaluation.entity_value import EntityValue, false_value
from mpl.lib.context_tree.context_tree_implementation import ContextTree, get_node_by_ref

ref_name = Union[str, Ref]

context_diff = Dict[str, Tuple[Optional[EntityValue], Optional[EntityValue]]]


def quick_diff(changes: Dict[Reference, EntityValue], old_context: ContextTree) -> context_diff:
    return {
        name: (old_context[name], changes.get(name))
        for name in changes if name != Reference.ROOT()
    }


@dataclasses.dataclass
class EngineContext:
    """
    EngineContext are immutable, any time you omake a change, you receive a new context along with the change manifest
    """
    tree: ContextTree = dataclasses.field(default_factory=ContextTree)

    def __getitem__(self, item: Reference) -> 'EntityValue':
        return self.tree[item]

    def __iter__(self) -> Iterator[Reference]:
        keys = set()
        for ref in self.tree:
            if not ref[0].is_void:
                keys.add(ref[0])
        return keys.__iter__()

    def __contains__(self, item: Reference) -> bool:
        return item in self.tree

    # region Modifiers
    # these methods return a new context with the changes applied

    def add(self, ref: ref_name, value: EntityValue) -> Tuple['EngineContext', context_diff]:
        new_tree = self.tree.__copy__()
        new_tree.add(ref, value)
        return EngineContext(new_tree), {}

    def set(self, ref: ref_name, value: EntityValue) -> Tuple['EngineContext', context_diff]:
        new_tree = self.tree.__copy__()
        changes = new_tree.change(ref, value)
        qd = quick_diff(changes, self.tree)
        return EngineContext(new_tree), qd

    def update(self, other: Dict[Reference, EntityValue] | 'EngineContext') -> Tuple['EngineContext', context_diff]:
        new_tree = self.tree.__copy__()
        match other:
            case EngineContext():
                other = other.to_dict()
        changes = new_tree.update(other, True)
        qd = quick_diff(changes, self.tree)
        return EngineContext(new_tree), qd

    def __or__(self, other: Dict[Reference, EntityValue] | 'EngineContext') -> 'EngineContext':
        result, _ = self.update(other)
        return result

    def clear(self, ref: Reference | Set[Reference]) -> Tuple['EngineContext', context_diff]:
        new_tree = self.tree.__copy__()
        changes = new_tree.clear(ref)
        qd = quick_diff(changes, self.tree)
        return EngineContext(new_tree), qd

    def activate(self, ref: ref_name | Set[ref_name], value=None) -> Tuple['EngineContext', context_diff]:
        if value is None:
            value = EntityValue.from_value(value or True)

        target_tree = self.tree.__copy__()
        changes = {}
        match ref:
            case Reference():
                changes |= target_tree.change(ref, value)
            case str():
                return self.activate(Ref(ref), value)
            case refs:
                for ref in refs:
                    changes |= target_tree.change(ref, value)

        qd = quick_diff(changes, self.tree)
        return EngineContext(target_tree), qd

    def deactivate(self, ref: ref_name | Set[ref_name]) -> Tuple['EngineContext', context_diff]:
        return self.activate(ref, EntityValue())

    # endregion

    @property
    def symbols(self) -> FrozenSet[Symbol]:
        result = set()
        for ref, value in self.tree:
            if ref.types and 'symbol' in ref.types and not value:
                result.add(ref.symbol)
        return frozenset(result)

    @property
    def active(self) -> Dict[Reference, EntityValue]:
        return {
            ref: value for ref, value in self.tree
            if value and not ref.is_void
        }

    @property
    def ref_names(self) -> FrozenSet[str]:
        return frozenset(item[0].name for item in self.tree)

    @staticmethod
    def from_graph(graph: MultiDiGraph) -> 'EngineContext':
        from mpl.interpreter.reference_resolution.mpl_ontology import Relationship

        references = frozenset({x for x in graph.nodes if isinstance(x, Reference)})
        typed_refs: Set[Reference] = set()
        for ref in references:
            type_edges = graph.out_edges(ref, data='relationship')
            types = {x[1] for x in type_edges if x[2] == Relationship.IS_A}
            this_ref = ref.with_types(types) if not ref == Ref('ROOT') else ref
            typed_refs.add(this_ref)
        return EngineContext.from_references(typed_refs)

    @staticmethod
    def from_dict(d: Dict[Reference, EntityValue]) -> 'EngineContext':
        tree = ContextTree.from_dict(d)
        return EngineContext(tree)

    @staticmethod
    def from_references(references: FrozenSet[Reference]) -> 'EngineContext':
        from mpl.interpreter.expression_evaluation.entity_value import EntityValue
        result = EngineContext()
        for ref in references:
            # TODO: this doesn't differentiate between different types of entities, e.g. triggers.
            #  Figure out how these should be handled in the  reference graph and update it here.

            result.tree.add(ref, false_value)

        return result

    @staticmethod
    def from_interpreter(interpreter: Union['ExpressionInterpreter', 'RuleInterpreter']) -> 'EngineContext':
        references = interpreter.references
        return EngineContext.from_references(references)

    def to_dict(self) -> Dict[Reference, 'EntityValue']:
        return self.tree.to_dict()

    @staticmethod
    def diff(
            initial_context: 'EngineContext',
            new_context: 'EngineContext'
    ) -> context_diff:
        c1_dict = initial_context.to_dict()
        c2_dict = new_context.to_dict()
        all_keys = set(c1_dict.keys()) | set(c2_dict.keys())
        result = dict()
        for key in all_keys:
            if key == Reference('ROOT'):
                continue
            v1 = c1_dict.get(key) or EntityValue()
            v2 = c2_dict.get(key) or EntityValue()
            if v1 == v2:
                continue
            result[key.name] = (v1, v2)

        return result

    def get_diff(self, other: 'EngineContext') -> context_diff:
        return EngineContext.diff(self, other)

    @property
    def whole_dict(self) -> Dict[Reference, 'EntityValue']:
        return {
            ref: value for ref, value in self.tree
            if not ref.is_void
        }

    @property
    def active_dict(self) -> Dict[Reference, 'EntityValue']:
        return {
            ref: value for ref, value in self.tree
            if value and not ref.is_void
        }

    def __str__(self):
        items = {}

        for ref in self.active:
            tmp = get_node_by_ref(self.tree.root, ref)
            if tmp.value:
                items[ref.name] = tmp.value

        lines = []
        for key, value in items.items():
            value_component = ','.join(str(x) for x in value)
            lines.append(f'{key}: {{{value_component}}}')
        sorted_lines = sorted(lines)
        return '\n'.join(sorted_lines)

    def __copy__(self):
        return EngineContext(self.tree.__copy__())

    def __hash__(self):
        return hash(self.tree)

    def __eq__(self, other):
        return self.tree == other.tree

    def __keys__(self):
        return self.tree.__keys__()
