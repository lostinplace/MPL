from dataclasses import dataclass

from parsita import TextParsers, reg, success

from lib.CustomParsers import best

"""
# Simple Value Tokenizer

This Parser defines the value tokens that are available in expressions

## Rules

> NUMBER = r/((?!-0?(\.0+)?(e|$))-?(0|[1-9]\d*)?(\.\d+)?(?<=\d)(e-?(0|[1-9]\d*))?|0x[0-9a-f]+)/
"""


@dataclass(frozen=True, order=True)
class NumberToken:
    content: str


"""
> RESERVED = r/^[A-Z]+$/
"""

@dataclass(frozen=True, order=True)
class ReservedToken:
    content: str


"""
> STRING = r/`([^`]|\\`)*`/
"""

@dataclass(frozen=True, order=True)
class StringToken:
    content: str


"""
> LABEL = r/[A-Za-z\s]+/
"""


@dataclass(frozen=True, order=True)
class LabelToken:
    content: str


def to(target_type):
    def result_func(parser_output):
        if isinstance(parser_output, str):
            parser_output = parser_output.strip()
        return target_type(parser_output)
    return result_func

# TODO: probably don't need this anymore
# def replace(pattern, replacement):
#     def outfunc(parser_output):
#         tmp = parser_output.replace(pattern, replacement).strip()
#         return success(tmp)
#     return outfunc


class SimpleValueTokenizers(TextParsers):
    number_token = reg(r"""((?!-0?(\.0+)?(e|$))-?(0|[1-9]\d*)?(\.\d+)?(?<=\d)(e-?(0|[1-9]\d*))?|0x[0-9a-f]+)""") \
                   > to(NumberToken)

    reserved_token = reg(r"[A-Z\-]+") > to(ReservedToken)

    string_token = '`' >> reg(r"""[^`]+""") << '`' > to(StringToken)

    label_token = reg(r"""[A-Za-z\s]+""") > to(LabelToken)

    token = best(number_token | reserved_token | string_token | label_token )





"""
# Advanced Value Tokenizer

TODO: Parameter should include dereference, arithmetic and method_invocation

> DEREFERENCE_PARAMETER = NUMBER | LABEL | STRING

Dereference_Parameter(value: U(Number, Label_Token, String_Expression) )

> DEREFERENCE_TOKEN = LABEL[INDEX_PARAMETER] (: RESERVED_TOKEN)?

Dereference_Token(label: Label_Token, index: Dereference_Parameter, type: Reserved_Token)

METHOD_PARAMETER = (LABEL\s*=\s*)? DEREFERENCE_PARAMETER

Method_Parameter(value: Dereference_Parameter, name: Label_Token, index: int)

> METHOD_INVOCATION = LABEL(repsep(METHOD_PARAMETER, ",")) (: RESERVED_TOKEN)?

Method_Invocation(method: Label_Token, args: List[Method_Parameter, returns: Reserved_Token)



"""