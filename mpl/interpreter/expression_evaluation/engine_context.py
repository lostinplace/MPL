import dataclasses
from collections import UserDict
from typing import FrozenSet, Dict, Union, Set

from sympy import Expr

from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference, Ref
from mpl.interpreter.expression_evaluation.interpreters import ExpressionInterpreter
from mpl.interpreter.reference_resolution.reference_graph_resolution import MPLEntity, MPLEntityClass

ref_name = Union[str, Ref]


class EngineContext(UserDict):
    ref_hashes: Dict[Reference, int] = {}
    hash_refs: Dict[int, Reference] = {}

    @staticmethod
    def from_references(references: FrozenSet[Reference]) -> 'EngineContext':
        result = EngineContext()
        for ref in references:
            ref_hash = hash(ref)
            result.ref_hashes[ref] = ref_hash
            result.hash_refs[ref_hash] = ref
            # TODO: this doesn't differentiate between different types of entities, e.g. triggers.
            #  Figure out how these should be handled in the  reference graph and updddate it here.
            entity = MPLEntity(ref_hash, ref.name, MPLEntityClass.STATE, frozenset())
            result[ref] = entity
        return result

    @staticmethod
    def from_interpreter(interpreter: ExpressionInterpreter) -> 'EngineContext':
        references = interpreter.references
        return EngineContext.from_references(references)

    def activate(self, ref: ref_name | Set[ref_name], value=None) -> 'EngineContext':
        match ref:
            case Reference():
                existing = self.get(ref)
                addition = value or hash(ref)
                new_value = existing.value | {addition}
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


