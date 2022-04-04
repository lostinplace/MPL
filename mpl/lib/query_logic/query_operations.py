from mpl.interpreter.expression_evaluation.entity_value import EntityValue
from mpl.lib.query_logic import false_result, true_result


def query_negate(operand: EntityValue) -> EntityValue:
    match operand:
        case EntityValue() as x if x.value:
            return false_result
        case EntityValue():
            return true_result
        case x if x:
            return false_result
    return true_result


def query_and(op1: EntityValue, op2: EntityValue) -> EntityValue:
    if op1 and op2:
        return op1 | op2

    return false_result


def query_or(op1: EntityValue, op2: EntityValue) -> EntityValue:
    if op1 or op2:
        return op1 | op2

    return false_result


def query_xor(op1: EntityValue, op2: EntityValue) -> EntityValue:
    if op1 and not op2:
        return op1

    if op2 and not op1:
        return op2

    return EntityValue()