import dataclasses
import enum
from dataclasses import dataclass
from numbers import Number
from typing import Dict, List, Tuple, Union

from parsita import TextParsers, reg, opt, Success, fwd, longest
from parsita.util import splat
from Parser.Tokenizers.simple_value_tokenizer import SimpleValueTokenizers as svt, NumberToken, StringToken

from lib.repsep2 import repsep2
import ast


#TODO:  This is gross, make it better
@dataclass(frozen=True, order=True)
class MPLVoid:
    pass





def inequal_compare(self, other: Union[Number, 'MPLVector'], operation: str = '__gt__'):
    if isinstance(other, Number):
        void_value = self.attributes.get(MPLVoid) or 1
        return void_value > other
    if isinstance(other, MPLVector):
        for k in other.attributes:
            other_val = other.attributes[k]
            this_val = self.attributes.get(k)
            if k == MPLVoid:
                this_val = this_val or 1
            if this_val < other_val:
                return False
        return True


class ComparisonResult(enum.Flag):
    none = enum.auto()
    lt = enum.auto()
    gt = enum.auto()
    eq = enum.auto()


@dataclass(frozen=True)
class MPLVector:
    attributes: Dict[
        Union[Number, MPLVoid, 'MPLVector', str],
        Union[Number, 'MPLVector']
    ] = dataclasses.field(default_factory=dict)

    def __bool__(self):
        return bool(self.attributes)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __compare__(self, other) -> ComparisonResult:
        if isinstance(other, Number):
            void_value = self.attributes.get(MPLVoid) or 1
            if void_value == other:
                return ComparisonResult.eq
            elif void_value > other:
                return ComparisonResult.gt
            elif void_value < other:
                return ComparisonResult.lt
        if isinstance(other, MPLVector):
            result = ComparisonResult.none
            for k in other.attributes:
                this_val = self.attributes.get(k)
                other_val = other.attributes[k]
                if k == MPLVoid:
                    this_val = this_val or 1
                if this_val == other_val:
                    result |= ComparisonResult.eq
                if this_val < other_val:
                    result |= ComparisonResult.lt
                if this_val > other_val:
                    result |= ComparisonResult.gt
            if len(self.attributes) == len(other.attributes):
                result |= ComparisonResult.eq
            if len(self.attributes) < len(other.attributes):
                result |= ComparisonResult.lt
            if len(self.attributes) > len(other.attributes):
                result |= ComparisonResult.gt
            return result ^ ComparisonResult.none

    def __ge__(self, other: Union[Number, 'MPLVector']):
        comparison_result = self.__compare__(other)
        return comparison_result | ComparisonResult.gt == ComparisonResult.gt | ComparisonResult.eq

    def __le__(self, other: Union[Number, 'MPLVector']):
        comparison_result = self.__compare__(other)
        return comparison_result | ComparisonResult.lt == ComparisonResult.gt | ComparisonResult.eq

    def __gt__(self, other: Union[Number, 'MPLVector']):
        comparison_result = self.__compare__(other)
        return comparison_result | ComparisonResult.eq == ComparisonResult.gt | ComparisonResult.eq

    def __lt__(self, other: Union[Number, 'MPLVector']):
        comparison_result = self.__compare__(other)
        return comparison_result | ComparisonResult.eq == ComparisonResult.lt | ComparisonResult.eq

    def __hash__(self):
        hashed_values = map(lambda x: (x[0], hash(x[1])), self.attributes.items())
        result = frozenset(hashed_values)
        return hash(result)

    def __radd__(self, other):
        return self + other

    def __add__(self, other):
        pass


def to_simple_vector(name, void_value, value: Number):
    if void_value != 1:
        return MPLVector({
            name: 1,
            MPLVoid: void_value
        }), value
    else:
        return MPLVector({
            name: value
        })


def to_complex_vector_component(vector, value):
    return vector, value


def to_vector_from_component_list(parse_result: List[MPLVector]):
    out_attributes = dict()
    for item in parse_result:
        if isinstance(item, MPLVector):
            void_value = item.attributes.get(MPLVoid)
            if void_value and void_value != 1:
                out_attributes[item] = 1
            else:
                tmp_attributes = item.attributes.items()
                out_attributes |= tmp_attributes
        elif isinstance(item, Tuple):
            k = item[0]
            v = item[1]
            out_attributes[k] = v
    return MPLVector(out_attributes)


# not done
def to_vector(vector: MPLVector, value: MPLVector | StringToken | NumberToken):
    void_value = {MPLVoid: value} if value != 1 else {}
    new_attributes = vector.attributes | void_value
    return MPLVector(dict(new_attributes))


# not done
def to_value(result: List[NumberToken | StringToken | MPLVector]) -> Number | str:
    if not result:
        return 1
    result = result[0]
    if isinstance(result, StringToken):
        return result.content
    if isinstance(result, str):
        return result
    elif isinstance(result, NumberToken):
        return ast.literal_eval(result.content)
    elif isinstance(result, MPLVector):
        return result
    return 1


class MPLVectorParsers(TextParsers):
    name = reg(r'[a-zA-Z\d]+')

    vector = fwd()

    value = longest(svt.number_token, name, vector)
    qualifier_value = opt('*' >> value) > to_value
    void_value = opt('#' >> value) > to_value

    simple_vector_component = name & void_value & qualifier_value > splat(to_simple_vector)
    complex_vector_component = vector & qualifier_value > splat(to_complex_vector_component)

    vector_component_list = '{' >> \
                            repsep2(longest(simple_vector_component, complex_vector_component), ',', min=1) \
                            << '}' \
                            > to_vector_from_component_list

    tmp_vector = vector_component_list & void_value > splat(to_vector)

    vector.define(tmp_vector)


def qv(content: str) -> MPLVector:
    result = MPLVectorParsers.vector.parse(content)
    return result.value


def test_mpl_vector_inequality():
    assert qv('{x*5,y*{ok,dude}}') > qv('{x*5,y*{ok}}')
    assert not(qv('{x*5,y*{ok,dude}}') < qv('{x*5,y*{ok}}'))
    assert qv('{x*5,y*6}') > 0
    assert not(qv('{x*5,y*6}') < 0)
    assert qv('{x*5,y*6}') > qv('{x*5,y*5}')
    assert qv('{x*5,y*6}#2') > qv('{x*5,y*5}')
    assert not(qv('{x*5,y*6}#2') < qv('{x*5,y*5}'))
    assert qv('{x*5,y*ok}') > qv('{x*5}')


def test_parse_mpl_vector():
    """
    {x*test,y*6}  + {x*me,y*2} == {x*{test,me},y*8}
    :return:
    """

    expectations = {
        '{x*{test,me},y*8}': MPLVector(
            {
                'x': MPLVector({'test': 1, 'me': 1}),
                'y': 8,
            }
        ),
        '{Red*5,Any#Color*3}': MPLVector(
            {
                'Red': 5,
                MPLVector({'Any': 1, MPLVoid: 'Color'}): 3,
            }
        ),
        '{x*{test,me}#2,y*6}': MPLVector(
            {
                'x': MPLVector(
                    {
                        'test': 1,
                        'me': 1,
                        MPLVoid: 2
                    }
                ),
                'y': 6,
            }
        ),
        '{x*5,y*6,{z,x}#-4*5}#3': MPLVector(
            {
                'x': 5,
                'y': 6,
                MPLVector(
                    {
                        'z': 1,
                        'x': 1,
                        MPLVoid: -4
                    }
                ): 5,
                MPLVoid: 3,
            }
        ),

    }

    # MPLVectorParsers.plain_vector.parse()

    for content in expectations:
        actual = MPLVectorParsers.vector.parse(content)
        expected = expectations[content]

        assert isinstance(actual, Success)
        sorted_expectations = '\n'.join(map(repr, sorted(expected.attributes.items(), key=repr)))
        sorted_actual = '\n'.join(map(repr, sorted(actual.value.attributes.items(), key=repr)))
        assert sorted_actual == sorted_expectations

        assert actual == Success(expected)


"""


^
*
/
%
+
-
&
|
==
!=
>
>=
<
<=
"""
