import dataclasses
from collections import UserDict
from typing import FrozenSet, Dict, Union, Set, Tuple, Optional

from networkx import MultiDiGraph
from sympy import Expr

from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference, Ref
from mpl.interpreter.expression_evaluation.interpreters import ExpressionInterpreter
from mpl.interpreter.reference_resolution.mpl_entity import MPLEntity
from mpl.interpreter.rule_evaluation import RuleInterpreter, RuleInterpretation

ref_name = Union[str, Ref]

context_diff = Dict[str, Tuple[FrozenSet, FrozenSet]]


class EngineContext(UserDict):
    ref_hashes: Dict[Reference, int] = {}
    hash_refs: Dict[int, Reference] = {}

    @property
    def active(self) -> FrozenSet[Reference]:
        return frozenset(ref for ref in self if self.get(ref).value)

    @property
    def ref_names(self) -> FrozenSet[str]:
        return frozenset(ref.name for ref in self)

    @staticmethod
    def from_graph(graph: MultiDiGraph) -> 'EngineContext':
        references = frozenset({x for x in graph.nodes if isinstance(x, Reference)})
        return EngineContext.from_references(references)

    @staticmethod
    def from_references(references: FrozenSet[Reference]) -> 'EngineContext':
        result = EngineContext()
        for ref in references:
            ref_hash = hash(ref)
            result.ref_hashes[ref] = ref_hash
            result.hash_refs[ref_hash] = ref
            # TODO: this doesn't differentiate between different types of entities, e.g. triggers.
            #  Figure out how these should be handled in the  reference graph and update it here.
            entity = MPLEntity(ref.name, frozenset())
            result[ref] = entity
        return result

    @staticmethod
    def from_interpreter(interpreter: ExpressionInterpreter | RuleInterpreter) -> 'EngineContext':
        references = interpreter.references
        return EngineContext.from_references(references)

    def activate(self, ref: ref_name | Set[ref_name], value=None) -> 'EngineContext':
        match ref:
            case Reference():
                existing = self.get(ref)
                match value:
                    case None:
                        new_value = existing.value | {ref.id}
                    case frozenset() | set():
                        new_value = value
                    case _:
                        new_value = existing.value | {value}

                new_entity = dataclasses.replace(existing, value=new_value)

                return EngineContext(self | {ref: new_entity})
            case str():
                return self.activate(Ref(ref), value)
            case refs:
                result: EngineContext = self | {}
                for ref in refs:
                    result |= result.activate(ref, value)
                return result

    def deactivate(self, ref: ref_name | Set[ref_name]) -> 'EngineContext':
        return self.activate(ref, frozenset())

    def to_dict(self) -> Dict[Reference, MPLEntity | Expr]:
        return self.data

    def apply(self, interpretations: FrozenSet[RuleInterpretation]) -> 'EngineContext':
        sum_of_changes = dict()
        for interpretation in interpretations:
            sum_of_changes |= interpretation.changes
        return self | sum_of_changes

    @staticmethod
    def diff(
            initial_context: 'EngineContext',
            new_context: 'EngineContext'
    ) -> Dict[str, Tuple[FrozenSet, FrozenSet]]:
        out = dict()
        for key in new_context:
            old_entity = initial_context.get(key)
            new_entity = new_context.get(key)
            old_val = old_entity.value
            new_val = new_entity.value
            if old_val == new_val:
                continue
            diff = old_val, new_val
            out[key.name] = diff
        return out

    def get_diff(self, other: 'EngineContext') -> context_diff:
        return EngineContext.diff(self, other)



