import dataclasses
import math
from typing import Generic, Sequence, Union, Callable, Optional, List, Any

from parsita import Parser, Reader, StringReader, lit
from parsita.parsers import AlternativeParser
from parsita.state import Input, Output, Continue, Backtrack, Failure


class ExcludingParser(Generic[Input, Output], Parser[Input, Input]):
    def __init__(self, parser: Parser[Input, Output]):
        super().__init__()
        self.parser = parser
        parserdef = repr(parser)
        self.name_cb = lambda: f"anything but {parserdef}"
        self.length = len(repr(parser))

    def consume(self, reader: Reader[Input]):
        result = self.parser.consume(reader)
        value = ''
        if isinstance(result, Continue):
            return Backtrack(reader, self.name_cb)
        position = reader.position
        while position < len(reader.source):
            start = position
            tmp = reader.source[start:]
            tmp_reader = StringReader(tmp)
            status = self.parser.consume(tmp_reader)
            if isinstance(status, Continue):
                break
            else:
                value += reader.source[start]
                position += 1
                reader = reader.drop(1)
        if len(value) > 0:
            return Continue(reader, value)
        return Backtrack(reader, self.name_cb)

    def __repr__(self):
        return self.name_or_nothing() + 'excluding({})'.format(repr(self.parser))


def excluding(parser: Parser[Input, Output]) -> ExcludingParser:
    """Match anything unless it matches the provided parser

    This matches all text until text that is matched by the provided parser is encountered.

    Args:
        :param parser: a parser that parses terms that you don't want to capture
    """
    if isinstance(parser, str):
        parser = lit(parser)
    return ExcludingParser(parser)


class RepeatedAtLeastNParser(Generic[Input, Output], Parser[Input, Sequence[Output]]):
    def __init__(self, n: int, parser: Parser[Input, Output]):
        super().__init__()
        self.parser = parser
        self.n = n
        parserdef = repr(parser)
        self.name_cb = lambda: f"at least {n} {parserdef}"

    def consume(self, reader: Reader[Input]):
        result = []
        remainder = reader
        while not remainder.finished:
            status = self.parser.consume(remainder)
            if not isinstance(status, Continue):
                break
            remainder = status.remainder
            result.append(status.value)

        if len(result) >= self.n:
            return Continue(remainder, result)
        else:
            return Backtrack(reader, self.name_cb)

    def __repr__(self):
        return self.name_or_nothing() + f'at least {self.n} ({self.parser.name_or_repr()})'


def at_least(n: int, parser: [Input, Output]) -> RepeatedAtLeastNParser:
    """Match a parser at least n times

    This matches ``parser`` multiple times in a row. If it matches as least
    n times, it returns a list of values that represents each time ``parser`` matched. If it
    matches ``parser`` less than n times it fails.

    Args:
        :param parser: Parser or literal
        :param n: count of minimum matches
    """
    if isinstance(parser, str):
        parser = lit(parser)
    return RepeatedAtLeastNParser(n, parser)


class CheckParser(Generic[Input, Output], Parser[Input, Input]):
    def __init__(self, parser: Parser[Input, Output]):
        super().__init__()
        self.parser = parser
        parserdef = repr(parser)
        self.name_cb = lambda: f"to see {parserdef} before moving on"
        self.length = len(repr(parser))

    def consume(self, reader: Reader[Input]):
        result = self.parser.consume(reader)
        if isinstance(result, Continue):
            return Continue(reader, result.value)
        return result

    def __repr__(self):
        return self.name_or_nothing() + 'check({})'.format(repr(self.parser))


def check(parser: Parser[Input, Output]) -> ExcludingParser:
    """Evaluates to see if you're on the right track without consuming input

    This will match text against the provided parser, and continue if that parser can move forward, else it will backtrack

    Args:
        :param parser: a parser that parses terms that you want to make sure are present
    """
    if isinstance(parser, str):
        parser = lit(parser)
    return CheckParser(parser)


class DebugParser(Generic[Input, Output], Parser[Input, Output]):
    def __init__(
        self,
        parser: Parser[Input, Output],
        verbose: bool = False,
        callback: Callable[[Parser[Input, Output], Reader[Input]], None] = None,
    ):
        super().__init__()
        self.parser = parser
        self.verbose = verbose
        self.callback = callback
        self._parser_string = repr(parser)

    def consume(self, reader: Reader[Input]):
        if self.verbose:
            print(f"""Evaluating token {reader.next_token()} using parser {self._parser_string}""")

        if self.callback:
            self.callback(self.parser, reader)

        result = self.parser.consume(reader)

        if self.verbose:
            print(f"""Result {repr(result)}""")

        return result

    def __repr__(self):
        return self.name_or_nothing() + f"debug({self.parser.name_or_repr()})"


def debug(
    parser: Parser[Input, Output],
    *,
    verbose: bool = False,
    callback: Optional[Callable[[Parser[Input, Input], Reader[Input]], None]] = None,
) -> DebugParser:
    """Execute debugging hooks before a parser.
    This parser is used purely for debugging purposes. From a parsing
    perspective, it behaves identically to the provided ``parser``, which makes
    ``debug`` a kind of harmless wrapper around a another parser. The
    functionality of the ``debug`` comes from providing one or more of the
    optional arguments.
    Args:
        parser: Parser or literal
        verbose: If True, causes a message to be printed containing the
            representation of ``parser`` and the next token before the
            invocation of ``parser``. After ``parser`` returns, the
            ``ParseResult`` returned is printed.
        callback: If not ``None``, is invoked immediately before ``parser`` is
            invoked. This allows the use to inspect the state of the input or
            add breakpoints before the possibly troublesome parser is invoked.
    """
    if isinstance(parser, str):
        parser = lit(parser)
    return DebugParser(parser, verbose, callback)


class BestAlternativeParser(Generic[Input, Output], Parser[Input, Output]):
    def __init__(self, *parsers: Parser[Input, Output]):
        super().__init__()
        self.parsers = parsers

    def consume(self, reader: Reader[Input]):
        furthest = 0
        best_result = None
        for parser in self.parsers:
            result = parser.consume(reader)
            if not isinstance(result, Continue):
                continue

            if result.remainder.finished:
                this_result_distance = math.inf
            else:
                this_result_distance = result.farthest.position

            if this_result_distance > furthest:
                furthest = this_result_distance
                best_result = result

        if best_result is not None:
            return best_result
        else:
            return result

    def __repr__(self):
        names = []
        for parser in self.parsers:
            names.append(parser.name_or_repr())

        return f"best({'|'.join(names)})"


def best(*parsers: Parser[Input, Output]) -> BestAlternativeParser:
    """Will return the furthest progress from any list of parsers

    This will try each parser provided, and return the result of the one that made it the farthest

    Args:
        :param parsers: a list of parsers or a single AlternativeParser

    """
    processed_parsers = []
    for parser in parsers:
        if isinstance(parser, str):
            processed_parsers.append(lit(parser))
        else:
            processed_parsers.append(parser)
    first_parser = processed_parsers[0]
    if len(processed_parsers) == 1 and isinstance(first_parser, AlternativeParser):
        processed_parsers = first_parser.parsers
    return BestAlternativeParser(*processed_parsers)


# TODO:  sort out how tracking should look

@dataclasses.dataclass(frozen=True, order=True)
class ParseResult:
    value: Any
    start: int
    ParserName: str

class TrackParser(Generic[Input, Output], Parser[Input, Input]):
    def __init__(self, parser: Parser[Input, Output]):
        super().__init__()
        self.parser = parser
        parserdef = repr(parser)
        self.name_cb = lambda: f"tracking {parserdef}"
        self.length = len(repr(parser))

    def consume(self, reader: Reader[Input]):
        status = self.parser.consume(reader)

        if isinstance(status, Continue):
            result = ParseResult(
                status.value,
                reader.position,
                self.parser.name
            )
            return Continue(status.remainder, result)
        return status

    def __repr__(self):
        return self.name_or_nothing() + 'track({})'.format(repr(self.parser))


def track(parser: Parser[Input, Output]) -> ExcludingParser:
    """Tracks metadata about the result of the provided parser

    Args:
        :param parser: a parser that parses terms that you want to make sure are present
    """
    if isinstance(parser, str):
        parser = lit(parser)
    return TrackParser(parser)


class RepeatWithKeptSeparatorsParser(Generic[Input, Output], Parser[Input, Sequence[Output]]):
    def __init__(self, parser: Parser[Input, Output], separator: Parser[Input, Output]):
        super().__init__()
        self.parser = parser
        self.separator = separator

    def consume(self, reader: Reader[Input]):
        status = self.parser.consume(reader)

        if not isinstance(status, Continue):
            return Continue(reader, []).merge(status)
        else:
            output = [status.value]
            remainder = status.remainder
            while True:
                # If the separator matches, but the parser does not, the remainder from the last successful parser step
                # must be used, not the remainder from any separator. That is why the parser starts from the remainder
                # on the status, but remainder is not updated until after the parser succeeds.
                status = self.separator.consume(remainder).merge(status)
                if isinstance(status, Continue):
                    last_match = output.pop()
                    separator_value = status.value
                    result = (last_match, separator_value)
                    status = self.parser.consume(status.remainder).merge(status)
                    if isinstance(status, Continue):
                        if remainder.position == status.remainder.position:
                            raise RuntimeError(remainder.recursion_error(str(self)))

                        remainder = status.remainder
                        output.append(result)
                        output.append(status.value)
                    else:
                        return Continue(remainder, output).merge(status)
                else:
                    return Continue(remainder, output).merge(status)

    def __repr__(self):
        return self.name_or_nothing() + f"repsep({self.parser.name_or_repr()}, {self.separator.name_or_repr()})"


def repwksep(
    parser: Union[Parser, Sequence[Input]], separator: Union[Parser, Sequence[Input]]
) -> RepeatWithKeptSeparatorsParser:
    """Match a parser zero or more times separated by another parser, and keeps the separators.

    This matches repeated sequences of ``parser`` separated by ``separator``. A
    list is returned containing tuples of matched values and separators If there are no matches, an empty
    list is returned.

    Args:
        :param parser: Parser or literal
        :param separator: Parser or literal
    """
    if isinstance(parser, str):
        parser = lit(parser)
    if isinstance(separator, str):
        separator = lit(separator)
    return RepeatWithKeptSeparatorsParser(parser, separator)


class SeparatedList(list):
    separators: List[Any] = None


class RepeatedSeparatedParser2(Generic[Input, Output], Parser[Input, Sequence[Output]]):
    def __init__(self,
                 parser: Parser[Input, Output],
                 separator: Parser[Input, Output],
                 min: Optional[int]=None,
                 max: Optional[int] = None,

                 ):
        super().__init__()
        self.parser = parser
        self.separator = separator
        self.repetition_minimum = min
        self.repetition_maximum = max

    def consume(self, reader: Reader[Input]):
        output = []
        separators = []
        active_separator = None
        remainder = reader
        status = self.parser.consume(reader)
        while isinstance(status, Continue):
            if self.repetition_maximum and self.repetition_maximum < len(output):
                message = f"repetition count maximum {self.repetition_maximum} exceeded for {self.name_or_nothing()}"
                return Backtrack(reader, lambda: message)

            active_separator = None
            if remainder.position == status.remainder.position:
                raise RuntimeError(remainder.recursion_error(str(self)))

            remainder = status.remainder
            output.append(status.value)

            # check for separator
            separator_status = self.separator.consume(remainder).merge(status)
            if not isinstance(separator_status, Continue):
                break

            remainder = separator_status.remainder
            active_separator = separator_status.value
            separators.append(active_separator)

            status = self.parser.consume(remainder).merge(status)

        # note that this is tricksy, any separator that is truthy will trigger failure state
        if active_separator:
            return status

        output_list = SeparatedList(output)
        output_list.separators = separators

        if self.repetition_minimum and self.repetition_minimum > len(output):
            message = f"repetition count minimum {self.repetition_minimum} not met for {self.name_or_nothing()}"
            return Backtrack(reader, lambda: message)

        result_status = Continue(remainder, output_list).merge(status)
        result_status.separators = separators
        result_status.value.separators = separators

        return result_status

    def __repr__(self):
        return self.name_or_nothing() + f"repsep2({self.parser.name_or_repr()}, {self.separator.name_or_repr()})"



def repsep2(
    parser: Union[Parser, Sequence[Input]], separator: Union[Parser, Sequence[Input]],
        min:Optional[int]=None,
        max:Optional[int]=None,
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
    """
    if isinstance(parser, str):
        parser = lit(parser)
    if isinstance(separator, str):
        separator = lit(separator)
    return RepeatedSeparatedParser2(parser, separator, min, max)