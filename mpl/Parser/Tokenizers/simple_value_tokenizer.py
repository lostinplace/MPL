import re
from dataclasses import dataclass

from parsita import TextParsers, reg, longest, success, failure

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
> STRING = r/`([^`]|\\`)*`/
"""

@dataclass(frozen=True, order=True)
class StringToken:
    content: str


"""
> LABEL = r/[A-Za-z ]+/
"""


@dataclass(frozen=True, order=True)
class ReferenceToken:
    content: str


def to(target_type):
    def result_func(parser_output):
        if isinstance(parser_output, str):
            parser_output = parser_output.strip()
        return target_type(parser_output)
    return result_func


base_reference_requirement_pattern = re.compile(r'[A-Za-z]')


def to_reference_token(result):
    tmp = result.strip()
    match = base_reference_requirement_pattern.match(tmp)
    if match:
        return success(ReferenceToken(tmp))
    else:
        return failure("needs at least 1 letter")


class SimpleValueTokenizers(TextParsers, whitespace=r'[ \t]*'):
    number_token = reg(r"""((?!-0?(\.0+)?(e|$))-?(0|[1-9]\d*)?(\.\d+)?(?<=\d)(e-?(0|[1-9]\d*))?|0x[0-9a-f]+)""") \
                   > to(NumberToken)

    string_token = '`' >> reg(r"""[^`]+""") << '`' > to(StringToken)

    reference_token = reg(r"""[\w ]+""") >= to_reference_token

    token = longest(number_token, string_token, reference_token)
