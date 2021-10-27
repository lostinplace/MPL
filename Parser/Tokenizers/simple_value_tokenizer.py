from dataclasses import dataclass

from parsita import TextParsers, reg, success, longest

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


class SimpleValueTokenizers(TextParsers):
    number_token = reg(r"""((?!-0?(\.0+)?(e|$))-?(0|[1-9]\d*)?(\.\d+)?(?<=\d)(e-?(0|[1-9]\d*))?|0x[0-9a-f]+)""") \
                   > to(NumberToken)

    reserved_token = reg(r"[A-Z\-]+") > to(ReservedToken)

    string_token = '`' >> reg(r"""[^`]+""") << '`' > to(StringToken)

    label_token = reg(r"""[A-Za-z\s]+""") > to(LabelToken)

    token = longest(number_token, reserved_token, string_token, label_token)
