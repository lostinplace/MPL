import logging
from numbers import Number
from typing import Union, FrozenSet, Tuple

from sympy import Expr


class Valuable:
    value: Union[str, Number, Expr]


class Machine(Valuable):
    states: FrozenSet['Machine', 'State']
    pass


class Context(dict):
    def __init__(self, *args):
        dict.__init__(self, args)

    def __getitem__(self, key):
        val = dict.__getitem__(self, key)
        logging.info("GET %s['%s'] = %s" % str(dict.get(self, 'name_label')), str(key), str(val))
        return val

    def __setitem__(self, key, val):
        logging.info("SET %s['%s'] = %s" % str(dict.get(self, 'name_label')), str(key), str(val))
        dict.__setitem__(self, key, val)


class Expression:
    pass



class Rule:
    expressions: Tuple[Expression]


class State(Valuable):
    states: FrozenSet['State']
    pass


class Wumpus(Machine):
    class Health(State):
        Ok: State
        Hurt: State
        Dead:  State