from typing import Generic, Sequence

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
        return self.name_or_nothing() + 'not({})'.format(repr(self.parser))


def excluding(parser: Parser[Input, Output]) -> ExcludingParser:
    """Match all except that which matches the provided parser

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

    This will match text against the provided parser, and accept if that parcer can move forward, else it will backtrack

    Args:
        :param parser: a parser that parses terms that you want to make sure are present
    """
    if isinstance(parser, str):
        parser = lit(parser)
    return CheckParser(parser)


class DebugParser(Generic[Input, Output], Parser[Input, Input]):
    def __init__(self, parser: Parser[Input, Output], verbose: bool = False):
        super().__init__()
        self.parser = parser
        self.parserdef = repr(parser)
        self.name_cb = lambda: f"to see {self.parserdef} before moving on"
        self.verbose = verbose
        self.breakpoint = breakpoint

    def consume(self, reader: Reader[Input]):
        evaluating = reader.source[reader.position:reader.position + 5]
        breakpoint()
        if self.verbose:
            print(f"""EVALUATING "{evaluating}..." FOR PARSER {self.parserdef}""")
            result = self.parser.consume(reader)
            print(f"""RESULT {repr(result)}""")
            return result
        else:
            result = self.parser.consume(reader)
            return result

    def __repr__(self):
        return self.name_or_nothing() + 'debug({})'.format(repr(self.parser))


def debug(parser: Parser[Input, Output], verbose: bool = False) -> DebugParser:
    """Lets you set breakpoints at print parser progress

    This will match text against the provided parser, and accept if that parcer can move forward, else it will backtrack

    Args:
        :param verbose: write progress messages to stdout
        :param breakpoint: set a breakpoint during execution
        :param parser: a parser that parses terms that you want to make sure are present
    """
    if isinstance(parser, str):
        parser = lit(parser)
    return DebugParser(parser, verbose)


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

        return f"greedy({'|'.join(names)})"


def best(*parsers: Parser[Input, Output]) -> BestAlternativeParser:
    """Will return the furthest prgoress from any list of parsers

    This will try each parsere provided, and return the result of the one that made it the farthest

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
