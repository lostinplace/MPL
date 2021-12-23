import itertools
from collections import defaultdict
from dataclasses import dataclass
from functools import reduce
from numbers import Number
from typing import Dict, Union, FrozenSet, List, Tuple, Any, Type, Callable

from Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpression
from Parser.ExpressionParsers.reference_expression_parser import Reference

from Tests import quick_parse
from interpreter.expression_evaluation.logical_expression_interpreter import postfix


@dataclass(frozen=True, order=True)
class TK:
    variable: Union[Reference, str, Number]
    exponent: Union[Reference, str, Number, 'MPLVector'] = 1

    def __rpow__(self, other):
        return self ** other

    def __pow__(self, power, modulo=None):
        match power:
            case int(_) | float(_):
                if isinstance(self.exponent, Number):
                    new_exponent = self.exponent * power
                    new_key = TK(self.variable, new_exponent)
                else:
                    power_as_vector = to_mpl_vector(power)
                    new_exponent = power_as_vector * self.exponent
                    new_key = TK(self.variable, new_exponent)
            case str(_) | Reference(_):
                if self.exponent == 1:
                    new_key = TK(self.variable, power)
                else:
                    power_as_vector = to_mpl_vector(power)
                    new_exponent = power_as_vector * self.exponent
                    new_key = TK(self.variable, new_exponent)
            case TK(_, _):
                if self.exponent == 1:
                    new_exponent = to_mpl_vector(power)
                else:
                    old_exponent = to_mpl_vector(self.exponent)
                    new_exponent = power * old_exponent
                new_key = TK(self.variable, new_exponent)
            case MPLVector(terms):
                evaluated = eval_mpl_vector(power)
                match (self.exponent, evaluated):
                    case 1, _:
                        new_exponent = evaluated
                    case _, 1:
                        new_exponent = self.exponent
                    case _, _:
                        new_exponent = self.exponent * evaluated

                new_key = TK(self.variable, new_exponent)
        return new_key

    def __radd__(self, other):
        return self+other

    def __add__(self, other):
        out = dict()
        self_as_key = frozenset([self])
        match other:
            case int(_) | float(_):
                out = {
                    self_as_key: 1,
                    frozenset([TK(1, 1)]): other
                }
            case TK(self.variable, self.exponent):
                out = {
                    self_as_key: 2
                }
            case TK(_, _):
                out = {
                    self_as_key: 1,
                    frozenset([other]): 1
                }
            case MPLVector(other_vars):
                item: TK
                for tmp_tk, tmp_mult in other_vars.items():
                    val = tmp_mult
                    if tmp_tk == self_as_key:
                        val = tmp_mult + 1
                    out[tmp_tk] = val
        return MPLVector(out)

    def __rmul__(self, other):
        return self * other

    def __mul__(self, other: Union[Number, 'TK', 'MPLVector']):
        out_vars = set()
        out_val = None
        match other:
            case int(_) | float(_):
                out_vars.add(self)
                out_val = other
            case TK(self.variable, _):
                tmp_exp = self.exponent + other.exponent
                k = TK(self.variable, tmp_exp)
                out_vars.add(k)
                out_val = 1
            case TK(_, _):
                out_vars.add(self)
                out_vars.add(other)
                out_val = 1
            case MPLVector(_):
                tmp = to_mpl_vector(self)
                return tmp * other
        out_dict = {
            frozenset(out_vars): out_val
        }
        return MPLVector(out_dict)


def is_scalar_vector(vector: 'MPLVector') -> bool:

    tks = vector.tks()
    if len(vector.terms) != 1:
        return False
    sole_tk = list(tks).pop()
    if sole_tk != TK(1,1):
        return False
    return vector.terms.get(tks)


def to_mpl_vector(item: Union[Number, str, Reference, TK, 'MPLVector']) -> 'MPLVector':
    match item:
        case MPLVector(_):
            return item
        case int(_) | float(_):
            tmp_key = to_tk(item)
            return MPLVector({
                fs(tmp_key): item
            })
        case str(_) | Reference(_, _):
            tmp_key = to_tk(item)
            return MPLVector({
                fs(tmp_key): 1
            })
        case TK(_, _):
            return MPLVector({
                fs(item): 1
            })

    raise NotImplementedError(f'could not get vector for type {type(item)}')


def prune_zero_terms(vector: 'MPLVector') -> 'MPLVector':
    filtered_terms = filter(lambda x: x[1], vector.terms.items())
    return MPLVector(dict(filtered_terms))


def to_tk(item: Union[Number, str, Reference] ) -> TK:
    match item:
        case int(_) | float(_):
            return TK(1, 1)
        case str(_) | Reference(_, _):
            return TK(item, 1)


@dataclass(frozen=True, order=True)
class MPLVector:
    terms: Dict[
        FrozenSet[TK],
        Number
    ]

    def tks(self):
        cache = set()
        for k in self.terms:
            cache |= k
        return frozenset(cache)

    def vars(self):
        out = frozenset([x.variable for x in self.tks() if not isinstance(x.variable, Number)])
        return out

    def __hash__(self):
        hashed_values = self.terms.items()
        result = frozenset(hashed_values)
        return hash(result)

    def __rtruediv__(self, other):
        return self / other

    def __truediv__(self, other):
        tmp = other ** -1
        return self * tmp

    def __rsub__(self, other):
        return self - other

    def __sub__(self, other):
        tmp = other * -1
        return self + tmp

    def __radd__(self, other):
        return self + other

    def __add__(self, other: Union[Number, str, 'MPLVector', TK, Reference]):
        match other:
            case 0 | 0.0:
                return self
            case int(_) | float(_):
                other_key = fs(TK(1, 1))
                existing_value = self.terms.get(other_key, 0)
                new_value = existing_value + other
            case str(_) | Reference(_, _):
                other_key = fs(TK(other, 1))
                existing_value = self.terms.get(other_key, 0)
                new_value = existing_value + 1
            case TK(_, _):
                other_key = fs(other)
                existing_value = self.terms.get(other_key, 0)
                new_value = existing_value + 1
            case MPLVector(_):
                out = dict()
                for key in other.terms:
                    old_value = self.terms.get(key, 0)
                    new_value = old_value + other.terms[key]
                    out[key] = new_value
                tmp = self.terms | out
                result = MPLVector(tmp)
                return prune_zero_terms(result)
        out = {
            other_key: new_value
        }
        result = MPLVector(self.terms | out)
        return prune_zero_terms(result)

    def __mul__(self, other: Union[Number, str, 'MPLVector', TK, Reference]) -> 'MPLVector':
        result = None
        match other:
            case 0 | 0.0:
                return MPLVector({})
            case 1 | 1.0:
                return self
            case int(_) | float(_):
                out = dict()
                for k in self.terms:
                    out[k] = self.terms[k] * other
                result =  MPLVector(out)
            case str(_) | Reference(_, _):
                tmp = to_mpl_vector(other)
                result =  mpl_vector_times_mpl_vector(tmp, self)
            case TK(_, _):
                result =  to_mpl_vector(other) * self
            case MPLVector(_):
                result = mpl_vector_times_mpl_vector(self, other)
        if result is not None:
            return prune_zero_terms(result)
        raise NotImplementedError(f"multiplication between MPL Vector and type {type(other)} is not supported")

    def __pow__(self, power):
        if len(self.terms) > 1:
            component_vectors = split_vector(self)
            cache = [x ** power for x in component_vectors]
            out = reduce(lambda x, y: x + y, cache)
            return prune_zero_terms(out)
        result = None
        match power:
            case 0 | 0.0:
                return to_mpl_vector(1)
            case 1 | 1.0:
                return self
            case int(_) | float(_):
                result = single_term_vector_up_number(self, power)
            case str(_) | Reference(_, _):
                result = single_term_vector_up_string_or_ref(self, power)
            case MPLVector(_):
                result = single_term_vector_up_vector(self, power)
        if result is not None:
            return prune_zero_terms(result)
        raise NotImplementedError(f"multiplication between MPL Vector and type {type(power)} is not supported")


def get_key_val_from_single_term_vector(vector: MPLVector) -> Tuple[FrozenSet[TK], Number]:
    key = set(vector.terms.keys()).pop()
    val = vector.terms[key]
    return key, val


def mpl_vector_times_mpl_vector(vec_a: MPLVector, vec_b: MPLVector ):
    scalar_key = fs(TK(1,1))
    distinct_terms_a = split_vector(vec_a)
    distinct_terms_b = split_vector(vec_b)

    cart_product = itertools.product(distinct_terms_a, distinct_terms_b)
    new_terms: List[MPLVector] = list()
    for op_a, op_b in cart_product:
        a_key, a_val = get_key_val_from_single_term_vector(op_a)
        b_key, b_val = get_key_val_from_single_term_vector(op_b)
        key_product = tk_set_times_tk_set(a_key, b_key)
        if len(key_product) > 1:
            key_product = key_product - scalar_key
        val_product = a_val * b_val
        vec_product = MPLVector({key_product: val_product})
        new_terms.append(vec_product)
    out = MPLVector({})
    for term in new_terms:
        out = out + term
    return out


def single_term_vector_up_vector(vector: MPLVector, power: MPLVector) -> MPLVector:
    power_as_single_terms = split_vector(power)
    sole_key: FrozenSet[TK] = set(vector.terms.keys()).pop()
    sole_value = vector.terms[sole_key]
    out_key = set()
    operations = itertools.product(sole_key, power_as_single_terms)
    new_value = 1
    for tk, power_vector in operations:
        if tk == TK(1, 1):
            tmp = eval_mpl_vector(power)
            if isinstance(tmp, Number):
                new_value = sole_value ** tmp
                new_key = TK(1, 1)
            else:
                new_key = TK(sole_value, power)
        else:
            new_key = tk ** power
        out_key.add(new_key)
    out = {
        frozenset(out_key): new_value
    }
    return MPLVector(out)


def single_term_vector_up_string_or_ref(vector: MPLVector, power: Union[str, Reference]) -> MPLVector:
    sole_key: FrozenSet[TK] = set(vector.terms.keys()).pop()
    sole_value = vector.terms[sole_key]
    out_key = set()
    if sole_key == fs(TK(1, 1)):
        new_key = TK(sole_value, power)
        out_key.add(new_key)
        out_value = 1
    else:
        out_value = 1
        if sole_value != 1:
            out_key.add(TK(sole_value, power))
        for tk in sole_key:
            match tk:
                case TK(var, 1):
                    new_key = TK(var, power)
                case TK(var, exponent):
                    new_exp = to_mpl_vector(power) * exponent
                    new_key = TK(var, new_exp)
            out_key.add(new_key)
    out = {
        frozenset(out_key): out_value
    }
    return MPLVector(out)


def single_term_vector_up_number(vector: MPLVector, power: Number) -> MPLVector:
    sole_key: FrozenSet[TK] = set(vector.terms.keys()).pop()
    sole_value = vector.terms[sole_key]
    out_key = set()
    if sole_key == fs(TK(1, 1)):
        out_key = sole_key
    else:
        for tk in sole_key:
            new_exp = tk.exponent * power
            new_key = TK(tk.variable, new_exp)
            out_key.add(new_key)
    out = {
        frozenset(out_key): sole_value ** power
    }
    return MPLVector(out)


# TODO: this needs to be tested
def eval_mpl_vector(op: MPLVector, context: Dict[Reference, Any] = dict()) -> Union[Number,MPLVector]:
    val = 0
    for term in op.terms:
        multiplier = op.terms[term]
        if multiplier == 0:
            continue
        var_value = eval_tk_set(term, context)
        match var_value,  multiplier:
            case x, y if isinstance(x, Number) and isinstance(y, Number):
                result = var_value * multiplier
            case frozenset(_), y:
                result = MPLVector({var_value: y})
            case x, y if isinstance(y, Number):
                tmp_key = fs(to_tk(x))
                result = MPLVector({tmp_key: y})
            case _, _:
                result = var_value * multiplier
        val = val + result
    return val


def vector_to_string(vector: MPLVector) -> str:
    """
    converts an MPL Vector to a readable expression
    :param vector:
    :return:
    """
    terms = []
    for term in vector.terms:
        components = []
        this_value = vector.terms[term]
        if this_value != 1:
            components.append(str(this_value))
        for component in term:
            exponent = component.exponent
            if exponent == 1:
                components.append(repr(component.variable))
            elif isinstance(component.exponent, MPLVector):
                tmp_exp = vector_to_string(component.exponent)
                tmp = fr"({component.variable} ^ ({tmp_exp}))"
                components.append(tmp)
            else:
                tmp = fr"({component.variable} ^ ({component.exponent}))"
                components.append(tmp)
        filtered = filter(lambda x: x != '1', components)
        sorted_components = sorted(filtered, key=lambda x: len(x))
        tmp = '*'.join(sorted_components)
        terms.append(tmp)

    sorted_terms = sorted(terms, key=lambda x: len(x))
    result = '+'.join(sorted_terms)
    return result


# TODO: this needs to be tested
def get_value_for_tk(item: TK, context: Dict[Reference, Any]) -> Union[Number, TK, str, Reference]:
    var = item.variable
    exp = item.exponent
    if isinstance(var, Reference) and var in context:
        var = context[var]
    if isinstance(exp, Reference) and exp in context:
        exp = context[var]
    if isinstance(exp, MPLVector):
        exp = eval_mpl_vector(exp, context)

    match var, exp:
        case _, 0:
            return 1
        case 1, _:
            return 1
        case out, 1:
            return out
        case str(_) | Reference(_, _), _:
            return TK(var, exp)
        case _, str(_) | Reference(_, _):
            return TK(var, exp)
        case x, y if isinstance(x, Number) and isinstance(y, Number):
            return var ** exp
        case _, MPLVector(_):
            return TK(var, exp)


# TODO: this needs to be teested
def eval_tk_set(op: FrozenSet[TK], context: Dict[Reference, Any]) -> \
        Union[Number, MPLVector, str, Reference, FrozenSet[TK]]:
    product = None
    for item in op:
        value = get_value_for_tk(item, context)
        match product, value:
            case None, _:
                product = value
            case x, y if isinstance(x, Number) and isinstance(y, Number):
                product *= value
            case _, _:
                product = product * value
    return product


def tk_set_times_tk_set(op_1: FrozenSet[TK], op_2: FrozenSet[TK]) -> FrozenSet[TK]:
    if op_2 == fs(TK(1, 1)):
        return op_1
    elif op_1 == fs(TK(1, 1)):
        return op_2
    combined = list(op_1) + list(op_2)
    cache = defaultdict(lambda: 0)
    for item in combined:
        operands = (cache[item.variable], item.exponent)
        match operands:
            case 0, y:
                cache[item.variable] = y
            case (MPLVector(_), _):
                cache[item.variable] += item.exponent
            case (x, y) if isinstance(x, Number) and isinstance(y, Number):
                cache[item.variable] += item.exponent
            case (x, y):
                tmp = to_mpl_vector(x)
                tmp = tmp + y
                cache[item.variable] = tmp
                pass
    result = [TK(x[0], x[1]) for x in cache.items()]
    return frozenset(result)


def split_vector(vector: MPLVector) -> List[MPLVector]:
    out = []
    for key in vector.terms:
        tmp = {
            key: vector.terms[key]
        }
        out.append(MPLVector(tmp))
    return out


def fs(*items) -> frozenset:
    return frozenset(tuple(items))


@dataclass(frozen=True, order=True)
class VectorOperation:
    symbol: str
    score: int
    allowed_types: Type
    method: Callable[[Any, Any], Any]


operations = [
    VectorOperation('^', 6, Number, lambda x, y: x ** y),
    VectorOperation('*', 5, Number, lambda x, y: x * y),
    VectorOperation('/', 5, Number, lambda x, y: x / y),
    VectorOperation('+', 4, Number, lambda x, y: x + y),
    VectorOperation('-', 4, Number, lambda x, y: x - y),
]

op_dict = dict(map(lambda x: (x.symbol, x), operations))


def postfix_to_vector(postfix_queue: List[Number | Reference | str]) -> MPLVector:
    index = 0
    while index < len(postfix_queue):
        item = postfix_queue[index]
        if item in op_dict:
            operation = op_dict[item]
            x = postfix_queue[index - 2]
            y = postfix_queue[index - 1]
            vec_x = to_mpl_vector(x)
            vec_y = to_mpl_vector(y)
            value = operation.method(vec_x, vec_y)
            postfix_queue[index] = value
            del postfix_queue[index-2:index]
            index -= 2
        else:
            index += 1
    assert len(postfix_queue) == 1
    return postfix_queue[0]


def to_vector(expression: ArithmeticExpression) -> MPLVector:
    postfixed = postfix(expression)
    return postfix_to_vector(postfixed)


def qv(input:str) -> MPLVector:
    expr = quick_parse(ArithmeticExpression, input)
    result = to_vector(expr)
    return result
