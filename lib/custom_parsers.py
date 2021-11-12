from typing import Generic, Sequence, Union, Callable, Optional

from parsita import Parser, Reader, StringReader, lit
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


class CheckParser(Generic[Input, Output], Parser[Input, Input]):
    def __init__(self, parser: Parser[Input, Output]):
        super().__init__()
        self.parser = parser

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


class LookbackParser(Generic[Input, Output], Parser[Input, Input]):
    def __init__(self, parser: Parser[Input, Output], limit: int = None):
        super().__init__()
        self.parser = parser
        parserdef = repr(parser)
        self.name_cb = lambda: f"look backward for {parserdef} in the stream before proceeding"
        self.limit = limit

    def consume(self, reader: Reader[Input]):

        source = reader.source
        end = reader.position
        start = end
        result = None

        while start > 0 and (self.limit is None or self.limit > end - start):
            start -= 1
            content = source[start:end]
            tmp_reader = StringReader(content)
            result = self.parser.consume(tmp_reader)
            if isinstance(result, Continue):
                if result.remainder.finished:
                    return Continue(reader, result.value)
                break

        return Backtrack(reader, self.name_cb)

    def __repr__(self):
        return self.name_or_nothing() + 'back({})'.format(repr(self.parser))


def back(parser: Parser[Input, Output], limit: int = None) -> ExcludingParser:
    """Evaluates to see if you're on the right track without consuming input

    This will match text against the provided parser, and continue if that parser can move forward, else it will backtrack

    Args:
        :param parser: a parser that parses terms that you want to make sure are present
    """
    if isinstance(parser, str):
        parser = lit(parser)
    return LookbackParser(parser, limit)


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
