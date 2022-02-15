"""
Warning:   This entire file is the rough equivalent of a fever dream that I had in response to the thought,
"type systems are hard, and I don't want to build one.  You know what everyone knows and isn't that hard?  Algebra!"
I'm not proud of it, but I guess it's done, so I'll use it  until I can prove it's a horrible idea -CMW
"""
import dataclasses
import enum
import itertools
from collections import defaultdict
from dataclasses import dataclass
from functools import reduce
from numbers import Number
from typing import Dict, Union, FrozenSet, List, Tuple, Any, Type, Callable, Iterable

from mpl.Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpression
from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression
from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference

from Tests import quick_parse
from mpl.interpreter.expression_evaluation.query_expression_interpreter import postfix
from mpl.interpreter.reference_resolution.reference_graph_resolution import MPLEntity


class MPLAlgebra(enum.Flag):
    NUMERIC = enum.auto()
    BOOLEAN = enum.auto()


@dataclass(frozen=True, order=True)
class Factor:
    base: Union[Reference, str, Number]
    exponent: Union[Reference, str, Number, 'Factor', 'MPLVector'] = 1

    def as_key(self):
        return fs(self)


EMPTY_SET = frozenset()

FactorSet = FrozenSet[Factor]

ResultSet = FrozenSet[Union[Number, 'MPLVector', str]]

MPL_Context = Dict[Reference, Union[Number, str, 'MPLVector', MPLEntity]]


def freezeset(arg):
    match arg:
        case frozenset():
            return arg
        case str(x):
            return frozenset({x})
        case x if isinstance(x, Iterable):
            return frozenset(arg)
        case x:
            return frozenset((arg,))


@dataclass(frozen=True, order=True)
class BooleanOperationResult:
    value: ResultSet
    inverse: ResultSet = frozenset()

    @staticmethod
    def from_args(a, b=frozenset()):
        a = freezeset(a)
        b = freezeset(b)
        return BooleanOperationResult(a, b)

    def __bool__(self):
        return bool(self.value)

    def __or__(self, other):
        match other:
            case BooleanOperationResult():
                value = self.value | other.value
                inverse = self.inverse | other.inverse
                return BooleanOperationResult(value, inverse)
            case x:
                value = self.value | fs(x)
                return BooleanOperationResult(value)

    def __and__(self, other):
        match self.value, other.value:
            case x, y if x and y:
                return self | other
            case x, y if x and not y:
                return BOR.from_args({}, self.value | other.inverse)
            case x, y if y and not x:
                return BOR.from_args({}, self.inverse | other.value)
            case x, y if not (x or y):
                return BOR.from_args({}, self.inverse | other.inverse)

    def __invert__(self):
        return BooleanOperationResult(self.inverse, self.value)


BOR = BooleanOperationResult


def eval_boolean_factor(factor: Factor, context: MPL_Context) -> BooleanOperationResult | Factor:
    resolved_factor = resolve_against_context(factor, context)
    match resolved_factor:

        case Factor(Reference(), _):
            return resolved_factor
        case Factor(_, Reference()):
            return resolved_factor
        case Factor(Reference(), Reference()):
            return resolved_factor
        case Factor(x, Factor() as other):
            y = eval_boolean_factor(other, context)
            tmp = Factor(x, y)
            return eval_boolean_factor(tmp, context)
        case Factor(x, y) if not (x or y):
            return BOR.from_args(1)
        case Factor(x, BOR() as y) if x and y:
            return y | x
        case Factor(x, MPLVector() as y) if x:
            raise NotImplementedError("haven't implemented vectors yet")
        case Factor(x, MPLEntity() as y) if x:
            raise NotImplementedError("haven't implemented entities yet")
        case Factor(x, y) if x and y:
            result = fs(x, y)
            return BOR.from_args(result)
        case Factor(x, y):
            inverse = x or y
            return BOR.from_args({}, inverse)


def eval_boolean_factor_set(factors: FactorSet, context: MPL_Context) -> BooleanOperationResult:
    out: BooleanOperationResult = None
    for factor in factors:
        factor_result = eval_boolean_factor(factor, context)
        match out, factor_result:
            case None, x:
                out = x
            case x, y:
                out = x & y
    return out


def eval_boolean_term(term: Tuple[FactorSet, Number], context: MPL_Context) -> BooleanOperationResult:
    out: BooleanOperationResult = eval_boolean_factor_set(term[0], context)
    scalar = term[1]
    match out, scalar:
        case x, 1:
            return x
        case x, -1:
            return ~x
        case _, 0:
            return BOR.from_args({})


def eval_boolean_vector(vector: 'MPLVector', context: MPL_Context):
    out: BooleanOperationResult = None
    for term in vector.terms.items():
        result = eval_boolean_term(term, context)
        match out, result:
            case None, x:
                out = x
            case x, y:
                out = x | y
    return out


def eval_numeric_factor(factor: Factor, context: MPL_Context):
    match factor:
        case Factor(Reference() as x, y):
            tmp = resolve_against_context(x, context)
            return eval_numeric_factor(Factor(tmp, y), context)
        case Factor(x, Reference() as y):
            tmp = resolve_against_context(y, context)
            return eval_numeric_factor(Factor(tmp, y), context)



def eval_factor_set(op: FrozenSet[Factor], context: Dict[Reference, Any]) -> \
        Union[Number, 'MPLVector', str, Reference, FrozenSet[Factor]]:
    product = None
    for item in op:
        value = get_value_for_factor(item, context)
        match product, value:
            case None, _:
                product = value
            case x, y if isinstance(x, Number) and isinstance(y, Number):
                product *= value
            case _, _:
                product = product * value
    return product


CONSTANT_FACTOR = Factor(1, 1)


def is_scalar_vector(vector: 'MPLVector') -> bool:

    factors = vector.factors()
    if len(vector.terms) != 1:
        return False
    sole_factor = list(factors).pop()
    if sole_factor != Factor(1, 1):
        return False
    return vector.terms.get(factors)


def to_mpl_vector(item: Union[Number, str, Reference, Factor, 'MPLVector']) -> 'MPLVector':
    match item:
        case MPLVector(_):
            return item
        case int(_) | float(_):
            tmp_key = to_factor(item)
            return MPLVector({
                fs(tmp_key): item
            })
        case str(_) | Reference(_, _):
            tmp_key = to_factor(item)
            return MPLVector({
                fs(tmp_key): 1
            })
        case Factor(_, _):
            return MPLVector({
                fs(item): 1
            })

    raise NotImplementedError(f'could not get vector for type {type(item)}')


def prune_zero_terms(vector: 'MPLVector') -> 'MPLVector':
    filtered_terms = filter(lambda x: x[1], vector.terms.items())
    return MPLVector(dict(filtered_terms))


def to_factor(item: Union[Number, str, Reference] ) -> Factor:
    match item:
        case int(_) | float(_):
            return Factor(1, 1)
        case str(_) | Reference(_, _):
            return Factor(item, 1)


@dataclass(frozen=True, order=True)
class MPLVector:
    terms: Dict[
        FactorSet,
        Number
    ]
    algebra: MPLAlgebra = MPLAlgebra.NUMERIC
    open: bool = True
    references: FrozenSet[Reference] = frozenset()

    def factors(self):
        cache = set()
        for k in self.terms:
            cache |= k
        return frozenset(cache)

    def vars(self):
        out = frozenset([x.base for x in self.factors() if not isinstance(x.base, Number)])
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

    def close(self):
        result = prune_zero_terms(self)
        return dataclasses.replace(result, open=False)

    def __add__(self, other: Union[Number, str, 'MPLVector', Factor, Reference]):
        match other:
            case 0 | 0.0:
                return self
            case int(_) | float(_):
                other_key = fs(Factor(1, 1))
                existing_value = self.terms.get(other_key, 0)
                new_value = existing_value + other
            case str(_) | Reference(_, _):
                other_key = fs(Factor(other, 1))
                existing_value = self.terms.get(other_key, 0)
                new_value = existing_value + 1
            case Factor(_, _):
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
                return MPLVector(tmp)
        out = {
            other_key: new_value
        }
        return MPLVector(self.terms | out)

    def __mul__(self, other: Union[Number, str, 'MPLVector', Factor, Reference]) -> 'MPLVector':
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
                result = MPLVector(out)
            case str(_) | Reference(_, _):
                tmp = to_mpl_vector(other)
                result = mpl_vector_times_mpl_vector(tmp, self)
            case Factor(_, _):
                result = to_mpl_vector(other) * self
            case MPLVector(_):
                result = mpl_vector_times_mpl_vector(self, other)
        if result is not None:
            return result
        raise NotImplementedError(f"multiplication between MPL Vector and type {type(other)} is not supported")

    def __pow__(self, power):
        if len(self.terms) > 1:
            component_vectors = split_vector(self)
            cache = [x ** power for x in component_vectors]
            out = reduce(lambda x, y: x + y, cache)
            return out
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
            return result
        raise NotImplementedError(f"multiplication between MPL Vector and type {type(power)} is not supported")


def get_key_val_from_single_term_vector(vector: MPLVector) -> Tuple[FrozenSet[Factor], Number]:
    key = set(vector.terms.keys()).pop()
    val = vector.terms[key]
    return key, val


def mpl_vector_times_mpl_vector(vec_a: MPLVector, vec_b: MPLVector ):
    scalar_key = fs(Factor(1, 1))
    distinct_terms_a = split_vector(vec_a)
    distinct_terms_b = split_vector(vec_b)

    cart_product = itertools.product(distinct_terms_a, distinct_terms_b)
    new_terms: List[MPLVector] = list()
    for op_a, op_b in cart_product:
        a_key, a_val = get_key_val_from_single_term_vector(op_a)
        b_key, b_val = get_key_val_from_single_term_vector(op_b)
        key_product = factor_set_times_factor_set(a_key, b_key)
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
    sole_key: FrozenSet[Factor] = set(vector.terms.keys()).pop()
    sole_value = vector.terms[sole_key]
    out_key = set()
    operations = itertools.product(sole_key, power_as_single_terms)
    new_value = 1
    for factor, power_vector in operations:
        if factor == Factor(1, 1):
            tmp = eval_mpl_vector(power)
            if isinstance(tmp, Number):
                new_value = sole_value ** tmp
                new_key = Factor(1, 1)
            else:
                new_key = Factor(sole_value, power)
        else:
            new_key = factor ** power
        out_key.add(new_key)
    out = {
        frozenset(out_key): new_value
    }
    return MPLVector(out)


def single_term_vector_up_string_or_ref(vector: MPLVector, power: Union[str, Reference]) -> MPLVector:
    sole_key: FrozenSet[Factor] = set(vector.terms.keys()).pop()
    sole_value = vector.terms[sole_key]
    out_key = set()
    if sole_key == fs(Factor(1, 1)):
        new_key = Factor(sole_value, power)
        out_key.add(new_key)
        out_value = 1
    else:
        out_value = 1
        if sole_value != 1:
            out_key.add(Factor(sole_value, power))
        for factor in sole_key:
            match factor:
                case Factor(var, 1):
                    new_key = Factor(var, power)
                case Factor(var, exponent):
                    new_exp = to_mpl_vector(power) * exponent
                    new_key = Factor(var, new_exp)
            out_key.add(new_key)
    out = {
        frozenset(out_key): out_value
    }
    return MPLVector(out)


def single_term_vector_up_number(vector: MPLVector, power: Number) -> MPLVector:
    sole_key: FrozenSet[Factor] = set(vector.terms.keys()).pop()
    sole_value = vector.terms[sole_key]
    out_key = set()
    if sole_key == fs(Factor(1, 1)):
        out_key = sole_key
    else:
        for factor in sole_key:
            new_exp = factor.exponent * power
            new_key = Factor(factor.base, new_exp)
            out_key.add(new_key)
    out = {
        frozenset(out_key): sole_value ** power
    }
    return MPLVector(out)


# TODO: this needs to be tested
def eval_mpl_vector(op: MPLVector, context: Dict[Reference, Any] = dict()) -> Union[Number, MPLVector]:
    val = 0
    for term in op.terms:
        multiplier = op.terms[term]
        if multiplier == 0:
            continue
        var_value = eval_factor_set(term, context)
        match var_value,  multiplier:
            case x, y if isinstance(x, Number) and isinstance(y, Number):
                result = var_value * multiplier
            case frozenset(_), y:
                result = MPLVector({var_value: y})
            case x, y if isinstance(y, Number):
                tmp_key = fs(to_factor(x))
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
                components.append(repr(component.base))
            elif isinstance(component.exponent, MPLVector):
                tmp_exp = vector_to_string(component.exponent)
                tmp = fr"({component.base} ^ ({tmp_exp}))"
                components.append(tmp)
            else:
                tmp = fr"({component.base} ^ ({component.exponent}))"
                components.append(tmp)
        filtered = filter(lambda x: x != '1', components)
        sorted_components = sorted(filtered, key=lambda x: len(x))
        tmp = '*'.join(sorted_components)
        terms.append(tmp)

    sorted_terms = sorted(terms, key=lambda x: len(x))
    result = '+'.join(sorted_terms)
    return result


def resolve_against_context(
        ref: Reference | Factor,
        context: Dict[Reference, Any]
) -> Union[Number, str, MPLVector, MPLEntity]:
    match ref:
        case Reference():
            value = context.get(ref)
            if value is None:
                return ref
            return value
        case Factor(Reference() as x, Reference() as y):
            new_base = resolve_against_context(x, context)
            new_exponent = resolve_against_context(y, context)
        case Factor(Reference() as x, y):
            new_base = resolve_against_context(x, context)
            new_exponent = y
        case Factor(x, Reference() as y):
            new_base = x
            new_exponent = resolve_against_context(y, context)
        case Factor(x, Factor() as y):
            new_exponent_factor = resolve_against_context(y, context)
            new_base = x
            new_exponent = new_exponent_factor
        case Factor(x, y):
            new_base = x
            new_exponent = y

    return Factor(new_base, new_exponent)




# TODO: this isn't done
def get_value_for_factor(item: Factor, context: Dict[Reference, Any]) -> Union[Number, Factor, str, Reference]:
    var = item.base
    exp = item.exponent
    if isinstance(var, Reference):
        var = resolve_against_context(var,  context)
    if isinstance(exp, Reference):
        exp = resolve_against_context(var,  exp)

    if isinstance(exp, MPLVector):
        exp = eval_mpl_vector(exp, context)

    # TODO: someone could use this to load the var of a factor with an MPL vector

    match var, exp:
        case _, 0:
            return 1
        case 1, _:
            return 1
        case out, 1:
            return out
        case str(_) | Reference(_, _), _:
            return Factor(var, exp)
        case _, str(_) | Reference(_, _):
            return Factor(var, exp)
        case x, y if isinstance(x, Number) and isinstance(y, Number):
            return var ** exp
        case _, MPLVector(_):
            return Factor(var, exp)


# TODO: this needs to be tested
def eval_factor_set(op: FrozenSet[Factor], context: Dict[Reference, Any]) -> \
        Union[Number, MPLVector, str, Reference, FrozenSet[Factor]]:
    product = None
    for item in op:
        value = get_value_for_factor(item, context)
        match product, value:
            case None, _:
                product = value
            case x, y if isinstance(x, Number) and isinstance(y, Number):
                product *= value
            case _, _:
                product = product * value
    return product


def factor_set_times_factor_set(op_1: FrozenSet[Factor], op_2: FrozenSet[Factor]) -> FrozenSet[Factor]:
    if op_2 == fs(Factor(1, 1)):
        return op_1
    elif op_1 == fs(Factor(1, 1)):
        return op_2
    combined = list(op_1) + list(op_2)
    cache = defaultdict(lambda: 0)
    for item in combined:
        operands = (cache[item.base], item.exponent)
        match operands:
            case 0, y:
                cache[item.base] = y
            case (MPLVector(_), _):
                cache[item.base] += item.exponent
            case (x, y) if isinstance(x, Number) and isinstance(y, Number):
                cache[item.base] += item.exponent
            case (x, y):
                tmp = to_mpl_vector(x)
                tmp = tmp + y
                cache[item.base] = tmp
                pass
    result = [Factor(x[0], x[1]) for x in cache.items()]
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
    sign: str
    score: int
    allowed_types: Type
    method: Callable[[Any, Any], Any]


operations = [
    VectorOperation('^', 6, Number, lambda x, y: x ** y),
    VectorOperation('*', 5, Number, lambda x, y: x * y),
    VectorOperation('/', 5, Number, lambda x, y: x / y),
    VectorOperation('+', 4, Number, lambda x, y: x + y),
    VectorOperation('-', 4, Number, lambda x, y: x - y),
    VectorOperation('&&', 3, Number, lambda x, y: x and y),
]

op_dict = dict(map(lambda x: (x.sign, x), operations))


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
    expr = quick_parse(QueryExpression, input)
    result = to_vector(expr)
    return result
