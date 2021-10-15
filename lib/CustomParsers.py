from typing import Generic, Sequence, Union, Callable

from parsita import Parser, Reader, StringReader, lit
from parsita.parsers import AlternativeParser
from parsita.state import Input, Output, Continue, Backtrack


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


class DebugParser(Generic[Input, Output], Parser[Input, Input]):
    def __init__(
            self, parser: Parser[Input, Output], verbose: bool = False,
            callback: Callable[[Parser[Input, Input], Reader[Input]], None] = None
    ):
        super().__init__()
        self.parser = parser
        self.parserdef = repr(parser)
        self.name_cb = lambda: f"to see {self.parserdef} before moving on"
        self.verbose = verbose
        self.callback = callback

    def consume(self, reader: Reader[Input]):
        if self.callback:
            self.callback(self.parser, reader)
        if self.verbose:
            evaluating = reader.source[reader.position:reader.position + 5]
            print(f"""EVALUATING "{evaluating}..." FOR PARSER {self.parserdef}""")
            result = self.parser.consume(reader)
            print(f"""RESULT {repr(result)}""")
            return result
        else:
            result = self.parser.consume(reader)
            return result

    def __repr__(self):
        return self.name_or_nothing() + 'debug({})'.format(repr(self.parser))


def debug(
        parser: Parser[Input, Output], verbose: bool = False,
        callback: Callable[[Parser[Input, Input], Reader[Input]], None]  = None
) -> DebugParser:
    """Lets you set breakpoints and print parser progress

    You can use the verbose flag to print messages as the parser is being evaluated

    You can use the callback method to insert a callback that will execute before the parser is evaluated, the call will include the reader

    Args:
        :param parser: a parser that parses terms that you want to make sure are present
        :param verbose: write progress messages to stdout
        :param callback: calls this function before evaluating the provided parser
    """
    if isinstance(parser, str):
        parser = lit(parser)
    return DebugParser(parser, verbose, callback)


class BestAlternativeParser(Generic[Input, Output], Parser[Input, Output]):
    def __init__(self, *parsers: Parser[Input, Output]):
        super().__init__()
        self.parsers = parsers

    def consume(self, reader: Reader[Input]):
        results = []
        for parser in self.parsers:
            result = parser.consume(reader)
            if isinstance(result, Continue):
                results.append((result.remainder.position, result))
            else:
                results.append((result.farthest.position, result))

        sorted_results = [x[1] for x in sorted(results, key=lambda _: _[0], reverse=True)]
        result = next((x for x in sorted_results if isinstance(x, Continue)), None)
        if result is None:
            return sorted_results[0]
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


class TrackParser(Generic[Input, Output], Parser[Input, Input]):
    def __init__(self, parser: Parser[Input, Output]):
        super().__init__()
        self.parser = parser
        parserdef = repr(parser)
        self.name_cb = lambda: f"tracking the depth of {parserdef} before moving on"
        self.length = len(repr(parser))

    def consume(self, reader: Reader[Input]):
        result = self.parser.consume(reader)
        if isinstance(result, Continue):
            return Continue(result.remainder, [reader.position, result.value])
        return result

    def __repr__(self):
        return self.name_or_nothing() + 'track({})'.format(repr(self.parser))


def track(parser: Parser[Input, Output]) -> ExcludingParser:
    """Tracks the current depth of the start of the successful parser

    This will match text against the provided parser, and accept if that parser can move forward, else it will backtrack.
    the result it returns will include an integer that specifies the depth that the match began

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
        parser: Parser or literal
        separator: Parser or literal
    """
    if isinstance(parser, str):
        parser = lit(parser)
    if isinstance(separator, str):
        separator = lit(separator)
    return RepeatWithKeptSeparatorsParser(parser, separator)