import dataclasses
from typing import FrozenSet, Dict, Union, Set, Tuple, Optional

from networkx import MultiDiGraph

from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference, Ref
from mpl.interpreter.expression_evaluation.entity_value import EntityValue
from mpl.interpreter.expression_evaluation.interpreters import ExpressionInterpreter
from mpl.interpreter.rule_evaluation import RuleInterpreter, RuleInterpretation
from mpl.lib.context_tree.context_tree_implementation import ContextTree, apply_changes

ref_name = Union[str, Ref]

context_diff = Dict[str, Tuple[Optional[EntityValue], Optional[EntityValue]]]


@dataclasses.dataclass
class EngineContext:
    tree: ContextTree = ContextTree()

    def __getitem__(self, item: Reference) -> 'EntityValue':
        return self.tree[item]

    def __setitem__(self, key: Reference, value: EntityValue):
        match key:
            case Reference():
                self.tree[key] = value

    def update(self, other: Dict[Reference, EntityValue]) -> Dict[Reference, EntityValue]:
        return self.tree.update(other)

    def clear(self, ref: Reference | Set[Reference]) -> Dict[Reference, EntityValue]:
        return self.tree.clear(ref)

    @property
    def active(self) -> Dict[Reference, EntityValue]:
        return {ref: value for ref, value in self.tree if value}

    @property
    def ref_names(self) -> FrozenSet[str]:
        return frozenset(item[0].name for item in self.tree)

    @staticmethod
    def from_graph(graph: MultiDiGraph) -> 'EngineContext':
        references = frozenset({x for x in graph.nodes if isinstance(x, Reference)})
        return EngineContext.from_references(references)

    @staticmethod
    def from_references(references: FrozenSet[Reference]) -> 'EngineContext':
        from mpl.interpreter.expression_evaluation.entity_value import EntityValue
        result = EngineContext()
        for ref in references:
            # TODO: this doesn't differentiate between different types of entities, e.g. triggers.
            #  Figure out how these should be handled in the  reference graph and update it here.
            result.tree.add(ref, EntityValue(value=frozenset()))
        return result

    @staticmethod
    def from_interpreter(interpreter: ExpressionInterpreter | RuleInterpreter) -> 'EngineContext':
        references = interpreter.references
        return EngineContext.from_references(references)

    def activate(self, ref: ref_name | Set[ref_name], value=None) -> 'EngineContext':
        value = EntityValue.from_value(value)
        match ref:
            case Reference():
                new_tree = self.tree.__copy__()
                new_tree[ref] |= value
                return EngineContext(new_tree)
            case str():
                return self.activate(Ref(ref), value)
            case refs:
                new_tree = self.tree.__copy__()
                for ref in refs:
                    new_tree[ref] |= value
                return EngineContext(new_tree)

    def deactivate(self, ref: ref_name | Set[ref_name]) -> 'EngineContext':
        return self.activate(ref, EntityValue())

    def to_dict(self) -> Dict[Reference, 'EntityValue']:
        return self.tree.to_dict()

    def apply(self, interpretations: FrozenSet[RuleInterpretation]) -> 'EngineContext':
        new_tree = self.tree.__copy__()
        sum_of_changes = dict()
        for interpretation in interpretations:
            sum_of_changes |= interpretation.changes
        apply_changes(sum_of_changes, new_tree)
        return EngineContext(new_tree)

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
            v1 = c1_dict.get(key)
            v2 = c2_dict.get(key)
            result[key.name] = (v1, v2)

        return result

    def get_diff(self, other: 'EngineContext') -> context_diff:
        return EngineContext.diff(self, other)

    def __str__(self):
        items = [(x[0].name, x[1]) for x in self.active.items()]
        lines = []
        for key, value in items:
            value_component = ','.join(str(x) for x in value)
            lines.append(f'{key}: {{{value_component}}}')
        sorted_lines = sorted(lines)
        return '\n'.join(sorted_lines)

    def __copy__(self):
        return EngineContext(self.tree.__copy__())

