import inspect
from collections import defaultdict
from typing import Union, Tuple, Set

from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression
from mpl.Parser.ExpressionParsers.reference_expression_parser import ReferenceExpression
from mpl.Parser.ExpressionParsers.rule_expression_parser import RuleExpression
from mpl.Parser.Tokenizers.operator_tokenizers import MPLOperators, MPLOperator, ArithmeticOperator, QueryOperator


def get_host_path_from_current_frame():
    frames = []
    this_frame = inspect.currentframe()

    while this_frame:
        frames.append(this_frame)
        this_frame = this_frame.f_back

    this_frame = inspect.currentframe()
    while this_frame:

        if '__qualname__' in this_frame.f_locals:
            qualname = this_frame.f_locals['__qualname__']
            match qualname:
                case 'Rule' | 'State' | 'Trigger' | 'Machine':
                    pass
                case _:
                    fi = inspect.getframeinfo(this_frame, context=1)
                    # TODO: deal with multi-line rules
                    lineno = fi.lineno
                    return tuple(qualname.split('.')), lineno
        this_frame = this_frame.f_back
    return None, None


def get_tba_name() -> str:
    host_frame = inspect.currentframe().f_back.f_back
    hfi = inspect.getframeinfo(host_frame, context=1)
    # TODO: this is incredibly gross, it relies on appropriate formatting of assignment statements
    definition_line = hfi.code_context[0].strip()
    name = definition_line.split('=')[0].strip()
    return name


def rule_combine(
        first: Union[QueryExpression, RuleExpression, 'State', 'Observe'],
        second: Union[QueryExpression, RuleExpression, 'State', 'Observe'],
        operator: MPLOperator
        ) -> RuleExpression:

    result: RuleExpression
    match first, second:
        case State(), _:
            return rule_combine(first.query_expression(), second, operator)
        case _, State():
            return rule_combine(first, second.query_expression(), operator)
        case Observe() as x, _:
            real_first = x.observed
            return rule_combine(real_first, second, MPLOperators.CONSUME_LEFT)
        case _, Observe() as x:
            real_second = x.observed
            return rule_combine(first, real_second, MPLOperators.OBSERVE_LEFT)
        case QueryExpression() as x, QueryExpression() as y:
            result = RuleExpression(
                (x, y),
                (operator,)
            )
        case QueryExpression() as x, RuleExpression() as y:
            result = RuleExpression(
                (x, *y.clauses),
                (operator, *y.operators)
            )
        case RuleExpression() as x, QueryExpression() as y:
            result = RuleExpression(
                (*x.clauses, y),
                (*x.operators, operator)
            )
        case RuleExpression() as x, RuleExpression() as y:
            result = RuleExpression(
                (*x.clauses, *y.clauses),
                (*x.operators, operator, *y.operators)
            )
        case _, _:
            raise TypeError(f"Cannot combine {first} and {second}")

    return result


def expression_op_combine(
        first: Union['State', QueryExpression],
        second: Union['State', QueryExpression],
        operator: ArithmeticOperator | QueryOperator) -> QueryExpression:
    from mpl.Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpression

    result: QueryExpression
    match first, second, operator:
        case State(), State(), QueryOperator():
            result = QueryExpression(
                (first.reference_expression(), second.reference_expression()),
                (operator,)
            )
        case State(), QueryExpression() as x, QueryOperator():
            result = QueryExpression(
                (first.reference_expression(), second),
                (operator,)
            )
        case QueryExpression(), State(), QueryOperator():
            result = QueryExpression(
                (first, second.reference_expression()),
                (operator,)
            )
        case QueryExpression(), QueryExpression(), QueryOperator():
            result = QueryExpression(
                (first, second),
                (operator,)
            )
        case State(), State(), ArithmeticOperator():
            result = QueryExpression(
                (ArithmeticExpression(
                    (first.reference_expression(), second.reference_expression()),
                    (operator,)
                ),),
                ()
            )
        case State(), ArithmeticExpression() as y, ArithmeticOperator():
            result = QueryExpression(
                (ArithmeticExpression(
                    (first.reference_expression(), y),
                    (operator,)
                ),),
                ()
            )
        case ArithmeticExpression() as x, State(), ArithmeticOperator():
            result = QueryExpression(
                (ArithmeticExpression(
                    (x, second.reference_expression()),
                    (operator,)
                ),),
                ()
            )
        case ArithmeticExpression() as x, ArithmeticExpression() as y, ArithmeticOperator():
            result = QueryExpression(
                (ArithmeticExpression(
                    (x, y),
                    (operator,)
                ),),
                ()
            )
        case _, _, _:
            raise TypeError(f"Cannot combine {first} and {second} with {operator}")
    return result


class State:

    def __init__(self, name=None):
        from uuid import uuid4
        self._host_id = uuid4()

        if name is None:
            name = get_tba_name()

        host_name, lineno = get_host_path_from_current_frame()

        if isinstance(self, Machine):
            self._qualified_name = (self._machine_name,)
        else:
            self._qualified_name = host_name + (name,)

    def reference_expression(self) -> ReferenceExpression:
        return ReferenceExpression(self._qualified_name)

    def query_expression(self) -> QueryExpression:
        return QueryExpression(
            (self.reference_expression(),),
            ()
        )

    def __invert__(self):
        return Observe(self)

    def __rshift__(self, other: Union[QueryExpression, 'State', RuleExpression]) -> RuleExpression:
        new_rule = rule_combine(self, other, MPLOperators.CONSUME_LEFT)
        add_rule_to_cache(new_rule)
        return new_rule

    def __and__(self, other):
        return expression_op_combine(self, other, QueryOperator('&'))

    def __or__(self, other):
        return expression_op_combine(self, other, QueryOperator('|'))

    def __xor__(self, other):
        return expression_op_combine(self, other, QueryOperator('^'))

    def __mul__(self, other: Union['State', QueryExpression]) -> QueryExpression:
        return expression_op_combine(self, other, ArithmeticOperator('*'))

    def __truediv__(self, other: Union['State', QueryExpression]) -> QueryExpression:
        return expression_op_combine(self, other, ArithmeticOperator('/'))

    def __add__(self, other: Union['State', QueryExpression]) -> QueryExpression:
        return expression_op_combine(self, other, ArithmeticOperator('+'))

    def __sub__(self, other: Union['State', QueryExpression]) -> QueryExpression:
        return expression_op_combine(self, other, ArithmeticOperator('-'))


def States() -> Tuple[State, ...]:
    name = get_tba_name()
    names = [name.strip() for name in name.split(',')]
    results = tuple(State(name) for name in names)
    return results


class Trigger(State):
    def __init__(self, name: str = None):
        if not name:
            host_frame = inspect.currentframe().f_back
            hfi = inspect.getframeinfo(host_frame, context=1)
            # TODO: this is incredibly gross
            definition_line = hfi.code_context[0].strip()
            name = definition_line.split('=')[0].strip()
        super().__init__(f'<{name}>')

    def expression(self) -> QueryExpression:
        return QueryExpression.parse(self._qualified_name)


class Machine(State):

    def __init__(self):
        # TODO need to figure out how to resolve descendant qualnames
        from uuid import uuid4
        uid = uuid4().hex

        new_machine_qualname = type(self).__qualname__
        self._machine_name = f'{new_machine_qualname}_{uid}'
        qual_name_parts = tuple(new_machine_qualname.split('.'))
        old_machine_path = qual_name_parts
        new_machine_path = qual_name_parts[:-1] + (self._machine_name,)
        new_machine_rules = rule_cache[qual_name_parts]

        tmp = inspect.getmembers(self)
        states = {new_machine_path + (x[0],): x[1] for x in tmp if isinstance(x[1], State)}

        new_rules = {}
        for lineno, rule in new_machine_rules.items():
            this_repr = repr(rule)
            rule_name = f'rule_{lineno}'
            requalified_rule = rule.requalify(old_machine_path, new_machine_path)
            requalified_repr = repr(requalified_rule)
            new_rules[rule_name] = requalified_rule

        setattr(self, '_rules', new_rules)
        setattr(self, '_states', states)
        super().__init__()

    def to_MPL(self) -> Set[str]:
        state_definitions = {'.'.join(path) for path in self._states.keys()}
        rule_definitions = {str(rule) for rule in self._rules.values()}
        return state_definitions | rule_definitions


rule_cache = defaultdict(dict)


def add_rule_to_cache(rule):
    hostname, lineno = get_host_path_from_current_frame()
    rule_cache[hostname][lineno] = rule


def get_expressions_for_host(host: Machine | State):
    # things that need to happen:
    # 1. get the host's qualname
    # 2. get the rules for that qualname
    # 3. generate unique name for the host (based on qualname and id)
    # 4. adjust the rules so that the host's qualname is replaced with the unique name
    # 5. get all of the substates for the host
    # 6. for each substate, get the rules for that substate (recursively)
    # 7. convert all substates into reference expressions
    # 8. convert all rules into rule expressions
    # 9. return the rules + reference expressions

    hostname, lineno = get_host_path_from_current_frame()
    return rule_cache[hostname].values()


class Accepts:
    def __init__(self, **kwargs):
        pass

    def __call__(self, dependent: State | Machine):
        return dependent


class Observe:
    observed: State | QueryExpression

    def __init__(self, observed: State | QueryExpression):
        self.observed = observed

    def __rshift__(self, other):
        new_rule = rule_combine(self.observed, other, MPLOperators.OBSERVE_LEFT)
        add_rule_to_cache(new_rule)
        return new_rule


#region Example

class BatteryMachine(State):
    pass


aliases = dict()


def Alias(name: str):
    tba_name = get_tba_name()
    host_name, lineno = get_host_path_from_current_frame()
    qualified_name = host_name + (name,)
    state = State(tba_name)
    aliases[qualified_name] = name
    return state


class Flashlight(Machine):

    On, Off = States()
    Button = Trigger()
    Light = Trigger()

    On >> Button >> Off
    Off >> Button >> On
    ~On >> Light


def test_thing():
    f = Flashlight()
    f_as_mpl = f.to_MPL()
    tmp = 1

# endregion