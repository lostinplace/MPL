from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference
from mpl.interpreter.expression_evaluation.entity_value import EntityValue, false_value


def target_and(op1: EntityValue, op2: EntityValue) -> EntityValue:
    """
    targets all references in op1 and op2
    """
    return op1 | op2


def target_xor(op1: EntityValue, op2: EntityValue) -> EntityValue:
    """
    this one is weird
    an active operand is activated with non-reference values
    this returns the active ooperand when the other is inactive

    if neither are active, returns the operand with references
    """

    one_refs = {x for x in op1.value if isinstance(x, Reference)}
    two_refs = {x for x in op2.value if isinstance(x, Reference)}
    one_vals = op1.value - one_refs
    two_vals = op2.value - two_refs

    if one_vals and two_vals:
        return false_value

    if one_vals and not two_vals:
        return op1

    if two_vals and not one_vals:
        return op2

    if not (one_vals or two_vals):
        if one_refs:
            return op1
        return op2

    return EntityValue()


def target_or(op1: EntityValue, op2: EntityValue) -> EntityValue:
    """
    the "doesn't matter" operator

    rrandommly choose operand 1 or 2

    """
    one_hash = hash(op1)
    two_hash = hash(op2)
    if one_hash > two_hash:
        return op1
    return op2