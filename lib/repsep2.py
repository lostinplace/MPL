import sys
from dataclasses import dataclass
from typing import Generic, Sequence, Optional, Union, List, Any, Tuple

from parsita import Parser, Reader, StringReader, lit
from parsita.state import Input, Output, Continue, Backtrack

from lib.additive_parsers import generate_subclass_with_attributes

tracked_repsep_result_cache = dict()


@dataclass
class RepSepMetadata:
    repetition: int


class RepeatedSeparatedParser2(Generic[Input, Output], Parser[Input, Sequence[Output]]):
    def __init__(self,
                 parser: Parser[Input, Output],
                 separator: Parser[Input, Output],
                 min: Optional[int] = 0,
                 max: Optional[int] = sys.maxsize,
                 reset: bool = False

                 ):
        super().__init__()
        self.parser = parser
        self.separator = separator
        self.repetition_minimum = min
        self.repetition_maximum = max
        self.reset = reset

    def consume(self, reader: Reader[Input]):
        output = []
        separators = []
        active_separator = None
        remainder = reader
        last_success = None
        status = self.parser.consume(reader)
        absolute_position = reader.position

        if not isinstance(status, Continue):
            return status

        while isinstance(status, Continue):
            if self.repetition_maximum < len(output):
                message = f"at most {self.repetition_maximum} for {self.name_or_nothing()}"
                return Backtrack(reader, lambda: message)

            if self.reset:
                absolute_position += status.remainder.position + 1

            output.append(status.value)
            infinite_recursion_risk = remainder.position == status.remainder.position
            remainder = status.remainder

            # check for separator
            active_separator = None
            separator_status = self.separator.consume(remainder).merge(status)
            if not isinstance(separator_status, Continue):
                break

            infinite_recursion_risk &= remainder.position == separator_status.remainder.position
            if infinite_recursion_risk:
                raise RuntimeError(remainder.recursion_error(str(self)))

            if self.reset:
                remainder_content = remainder.source[separator_status.remainder.position:]
                remainder = StringReader(remainder_content)
            else:
                remainder = separator_status.remainder
            active_separator = separator_status.value
            separators.append(active_separator)

            last_success = status
            status = self.parser.consume(remainder).merge(status)

        # note that this is tricksy, any separator that is truthy will trigger failure state
        if active_separator:
            status = last_success
            separators = separators[:-1]

        if self.repetition_minimum > len(output):
            message = f"at least {self.repetition_minimum} for {self.__repr__()}"
            return Backtrack(reader, lambda: message)

        output_list = SeparatedList(output)
        output_list.separators = tuple(separators)

        if self.reset:
            reader.position = absolute_position
            result_status = Continue(reader, output_list).merge(status)
        else:
            result_status = Continue(status.remainder, output_list).merge(status)

        return result_status

    def __repr__(self):
        return self.name_or_nothing() + f"repsep2({self.parser.name_or_repr()}, {self.separator.name_or_repr()})"


def repsep2(
    parser: Union[Parser, Sequence[Input]], separator: Union[Parser, Sequence[Input]],
        min:int = 0,
        max:int = sys.maxsize,
        reset: bool = False
) -> RepeatedSeparatedParser2:
    """Match a parser zero or more times separated by another parser.

    This matches repeated sequences of ``parser`` separated by ``separator``. A
    list is returned containing the value from each match of ``parser``. The
    values from ``separator`` are discarded. If there are no matches, an empty
    list is returned.

    Args:
        :param parser: Parser or literal
        :param separator: Parser or literal
        :param min: Minimum number of repetitions before the parser succeeds
        :param max: Maximum number of repetitions before the parser fails
        :param reset: if true, resets the reader after each separator
    """
    if isinstance(parser, str):
        parser = lit(parser)
    if isinstance(separator, str):
        separator = lit(separator)
    return RepeatedSeparatedParser2(parser, separator, min, max, reset)


# def recurse_hash_list(a_list):
#     out = []
#     for i in a_list:
#         if isinstance(i, Iterable):
#             out.append( recurse_hash_list(i) )
#         else:
#             out.append(hash(i))
#     return tuple(out)


class SeparatedList(tuple):
    separators: Tuple[Any] = None

    # def __hash__(self):
    #     hashed_values = recurse_hash_list(self.__iter__())
    #     hashed_separators = recurse_hash_list(self.separators)
    #     tmp = (hashed_values, hashed_separators)
    #     return hash(tmp)
