import dataclasses
from enum import Enum
from numbers import Number

from typing import Dict, FrozenSet, Optional, Tuple, Set

from sympy import Symbol

from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference, ReferenceExpression

from mpl.interpreter.expression_evaluation.entity_value import EntityValue


@dataclasses.dataclass(order=True)
class ContextTreeNode:
    ref: Reference = Reference('ROOT')
    value: EntityValue = EntityValue()
    children: Dict[str, 'ContextTreeNode'] = dataclasses.field(default_factory=dict)
    parent: Optional['ContextTreeNode'] = None

    def __getitem__(self, item: Reference) -> EntityValue:
        return get_value(self, item)

    @property
    def void_value(self) -> EntityValue:
        return EntityValue.from_value(1) if not self.entity else EntityValue()

    @property
    def entity(self) -> EntityValue:
        result = self.value
        for child in self.children.values():
            result |= child.entity
        return result

    def to_string(self, indent=0):
        self_str = '+' * indent + f'{self}'
        child_results = [x.to_string(indent + 1) for x in self.children.values()]
        child_block = '\n'.join(child_results)
        if child_block:
            return f'{self_str}\n{child_block}'
        return f'{self_str}'

    def __str__(self) -> str:
        return f'{self.ref}: {self.value}: {self.entity}'

    def __iter__(self):
        yield self.ref, self.entity
        yield self.ref.void, self.void_value
        for node in self.children.values():
            yield from node.__iter__()


@dataclasses.dataclass(order=True)
class ContextTree:
    root: ContextTreeNode = dataclasses.field(default_factory=ContextTreeNode)
    _keys: Optional[FrozenSet[Reference]] = None

    # region Modifiers

    # these are the only methods that should be used to modify the tree

    def clear(self, ref: Reference | FrozenSet[Reference]) -> Dict[Reference, EntityValue]:
        return clear_references(self.root, ref)

    def change(self, ref: Reference, value: EntityValue) -> Dict[Reference, EntityValue]:
        return change_node(self.root, ref, value)

    def update(self, other: Dict[Reference, EntityValue]) -> Dict[Reference, EntityValue]:
        result = dict()
        for ref, value in other.items():
            new_value = None
            match value:
                case _, EntityValue() as new:
                    new_value = new
                case EntityValue() as new:
                    new_value = new
            result |= self.change(ref, new_value)
        return result

    def add(self, ref: Reference, value: EntityValue):
        add_child(self.root, ref, value)
        self._keys = None

    #endregion

    def __contains__(self, item: Reference):
        return item in self.__keys__()

    def __keys__(self) -> FrozenSet[Reference]:
        if self._keys is None:
            self._keys = frozenset({x[0] for x in self.root.__iter__()})
        return self._keys

    def __iter__(self):
        yield from self.root.__iter__()

    def __getitem__(self, item: Reference) -> EntityValue | Symbol:
        return get_value(self.root, item)

    def to_dict(self):
        return tree_to_dict(self.root)

    @staticmethod
    def from_dict(d: Dict[Reference, str | Number | EntityValue]):
        root = tree_from_dict(d)
        return ContextTree(root)

    @property
    def entity(self) -> EntityValue:
        return self.root.entity

    def __copy__(self):
        root = copy_tree(self.root)
        return ContextTree(root, self._keys)

    def to_string(self):
        return self.root.to_string()

    def __str__(self):
        return f'ContextTree({self.to_string()})'


class OperationResult(Enum):
    SUCCESS = 0
    FAILURE = 1


def reference_is_child_of_reference(ref: Reference, potential_parent_ref: Reference) -> int:
    ref_expr = ref.expression
    ref_expr_length = len(ref_expr.path)
    if potential_parent_ref == Reference('ROOT'):
        return ref_expr_length
    parent_expr = potential_parent_ref.expression
    parent_expr_length = len(parent_expr.path)

    if parent_expr.path != ref_expr.path[:parent_expr_length]:
        return -1

    if ref_expr.path == parent_expr.path:
        return 0

    return ref_expr_length - parent_expr_length


def get_intermediate_child_ref(parent: Reference, ref: Reference, stages: int) -> Reference:
    ref_expr_path = ref.expression.path

    parent_length = len(parent.expression.path)
    if parent == Reference('ROOT'):
        target_count = stages
    else:
        target_count = parent_length + stages

    result_path = ref_expr_path[:target_count]
    result_expr = ReferenceExpression(result_path)
    return result_expr.reference


def add_child(node: ContextTreeNode, ref: Reference, value: EntityValue) -> OperationResult:
    if ref.is_void:
        return OperationResult.FAILURE
    relationship = reference_is_child_of_reference(ref, node.ref)
    match relationship:
        case -1:
            return OperationResult.FAILURE
        case 0:
            node.ref = dataclasses.replace(node.ref, types=ref.types | node.ref.types)
            return OperationResult.SUCCESS
        case 1:
            new_node = ContextTreeNode(ref, value, parent=node)
            node.children[ref.name] = new_node
            return OperationResult.SUCCESS
        case x if x > 1:
            intermediate_child_ref = get_intermediate_child_ref(node.ref, ref, 1)
            intermediate_child = node.children.get(intermediate_child_ref.name)
            if intermediate_child is None:
                add_child(node, intermediate_child_ref, EntityValue())
                intermediate_child = node.children[intermediate_child_ref.name]
            return add_child(intermediate_child, ref, value)


def refs_are_compatible(ref1: Reference, ref2: Reference) -> bool:
    if ref1.name != ref2.name:
        return False
    if not ref1.types or not ref2.types:
        return True
    return ref1.types.issubset(ref2.types)


def get_value(node: ContextTreeNode, ref: Reference) -> EntityValue:
    node = get_node_by_ref(node, ref)
    if node is None:
        return EntityValue()
    return node.entity


def get_node_by_ref(node: ContextTreeNode, ref: Reference) -> Optional[ContextTreeNode]:
    if refs_are_compatible(ref, node.ref):
        return node
    degree = reference_is_child_of_reference(ref, node.ref)
    if degree == -1:
        return None
    if degree == 1 and ref.is_void:
        value = EntityValue.from_value(1) if not node.entity else EntityValue()
        return ContextTreeNode(ref, value, parent=node)
    intermediate_child_ref = get_intermediate_child_ref(node.ref, ref, 1)
    intermediate_child = node.children.get(intermediate_child_ref.name)
    if intermediate_child is None:
        return None
    return get_node_by_ref(intermediate_child, ref)


def tree_from_dict(d: Dict[Reference, any]) -> ContextTreeNode:
    items = sorted(list(d.items()), key=lambda x: str(x[0]))
    root = ContextTreeNode(Reference('ROOT'))
    for ref, value in items:
        ev = EntityValue.from_value(value)
        add_child(root, ref, ev)
    return root


def tree_to_dict(node: ContextTreeNode) -> Dict[Reference, EntityValue]:
    result = {
        node.ref: node.entity
    }
    tmp = get_value(node, node.ref.void)
    if tmp:
        result[node.ref.void] = tmp

    for child in node.children.values():
        result |= tree_to_dict(child)

    return result


def change_node(node: ContextTreeNode, ref: Reference, value: EntityValue) -> Dict[Reference, EntityValue]:
    value = EntityValue.from_value(value)
    target_this_node = refs_are_compatible(ref, node.ref)

    if target_this_node and value:
        from_children = node.entity.without(node.value)
        not_handled_by_children = value.without(from_children)
        old_void = node.void_value
        node.value = not_handled_by_children
        output = {
            node.ref: node.entity
        }
        new_void = node.void_value
        if old_void != new_void:
            output[node.ref.void] = new_void
        return output
    elif target_this_node and not value:
        ref = node.ref.void
        value = EntityValue.from_value(1)

    degree = reference_is_child_of_reference(ref, node.ref)
    if degree == -1:
        return {}
    if degree == 1 and ref.is_void and value:
        node.value = EntityValue()
        changes = {
            ref: EntityValue.from_value(1),
            node.ref: EntityValue()
        }
        for child_ref_name, child_node in node.children.items():
            child_ref = Reference(child_ref_name)
            changes |= change_node(child_node, child_ref, EntityValue())
        return changes
    elif degree > 0:
        intermediate_child_ref = get_intermediate_child_ref(node.ref, ref, 1)
        intermediate_child = node.children.get(intermediate_child_ref.name)
        original_value = node.entity
        if intermediate_child is None:
            return {}
        changes = change_node(intermediate_child, ref, value)
        if node.entity != original_value:
            changes |= {node.ref: node.entity}
        return changes


def clear_references(node: ContextTreeNode, references: FrozenSet[Reference]) -> Dict[Reference, EntityValue]:
    changes = {}
    # TODO: figure out what it means to consume a void reference
    for item in references:
        if item.is_void:
            continue
        changes |= change_node(node, item, EntityValue())
    return changes


def copy_tree(node: ContextTreeNode | ContextTree, parent: Optional[ContextTreeNode] = None) -> ContextTreeNode:
    if isinstance(node, ContextTree):
        return copy_tree(node.root, None)
    result = ContextTreeNode(node.ref, parent=parent)
    result.value = node.value
    result.children = {
        child_name: copy_tree(child, node)
        for child_name, child in node.children.items()
    }
    return result


EntityContext = Dict[Reference, EntityValue]


def get_conflicts(context_a: EntityContext, context_b: EntityContext) \
        -> Set[Tuple[Reference, EntityValue, EntityValue]]:
    all_keys = set(context_a.keys()) | set(context_b.keys())
    conflicts = set()
    for key in all_keys:
        a = context_a.get(key)
        b = context_b.get(key)
        if a == b:
            continue
        if a is None or b is None:
            continue
        conflicts.add((key, a, b))
    return conflicts


def apply_changes(changes: Dict[Reference | str, EntityValue], node: ContextTreeNode, in_place=True) \
        -> Tuple['RuleInterpretationState', ContextTreeNode]:
    from mpl.interpreter.rule_evaluation import RuleInterpretationState

    if not in_place:
        new_node = copy_tree(node)
    else:
        new_node = node

    result = {}
    for ref, value in changes.items():
        if isinstance(ref, str):
            ref = Reference(ref)
        tmp = change_node(new_node, ref, value)
        conflicts = get_conflicts(tmp, result)
        if conflicts:
            return RuleInterpretationState.NOT_APPLICABLE, new_node
        result |= tmp
    return RuleInterpretationState.APPLICABLE, new_node
