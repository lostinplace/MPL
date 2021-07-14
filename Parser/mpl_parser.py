from dataclasses import replace

from parsita import *
from parsita.util import splat

from Parser.CustomParsers import debug
from Parser.mpl_parser_classes import Declaration, Event, State, default_state, Machine, Rule, Transition, \
    TransitionType, Trigger

from Parser.expression_parser import ExpressionParsers as E, Label, Expression
from Parser.arrow_parser import ArrowParser as A, Arrow


def process_declaration(name: Label, type: Label) -> Declaration:
    m = {
        'EVENT': Event,
        'STATE': State,
        'MACHINE': Machine,
    }
    t = m.get(type.name)
    result = None
    if not t:
        parent_state = State(type, None, False)
        result = State(name, parent_state, True)
    elif t is State:
        result = default_state(name.name)
    else:
        result = t(name)

    return Declaration(result)


### identify is left, and act is right
def process_mpl_rule(operations) -> Rule:
    from Parser.mpl_parser_classes import TransitionType as TT
    queue = list()
    operand_type = None
    operation = None
    for op in operations:
        operand = op[0]
        operator:Arrow = op[1] and op[1][0] or None
        result = None
        if operator == Arrow(None, '-', '>'):
            result = Transition(operand, None, TT.HARD)
        elif operator == Arrow('*', '-', '>'):
            result = Trigger(operand, None, TT.HARD)
        else:
            tmp = queue.pop(-1)
            result = replace(tmp, goal=operand)
        queue.append(result)
    return Rule(queue)


class MPLParser(TextParsers):
    declaration = E.label << ':' & E.label > splat(process_declaration)
    MPL_Operation = E.label & opt(A.arrow)
    rule = rep1(MPL_Operation) > process_mpl_rule
