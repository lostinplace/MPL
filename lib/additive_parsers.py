from dataclasses import dataclass, is_dataclass
from typing import Any, Generic, Dict, TypeVar, Union, Type, Tuple

from parsita import Parser, Reader, lit
from parsita.state import Status, Input, Output, Continue

from lib.custom_parsers import ExcludingParser


subclass_cache: Dict[Tuple[type, type], type] = dict()


def generate_subclass_with_attributes(instance: any, prefix:str, interface: type, attrs: Dict[str, Any]):
    result_type = type(instance)

    subclass_name = f'{prefix}{result_type.__name__}'
    cache_key = (result_type, interface)

    if cache_key in subclass_cache:
        result_subclass = subclass_cache[cache_key]
    else:
        result_subclass = type(subclass_name, (result_type, interface), attrs)
        subclass_cache[cache_key] = result_subclass

    if is_dataclass(instance):
        params = vars(instance)
        result_value = result_subclass(**params)
    else:
        result_value = result_subclass(instance)

    for k in attrs:
        setattr(result_value, k, attrs[k])
    return result_value


tracked_subclass_cache = dict()


@dataclass(frozen=True, order=True)
class TrackingMetadata:
    start: int
    parser_name: str
    status: Status[Input, Output]


class TrackedValue:
    metadata: TrackingMetadata


class TrackParser(Generic[Input, Output], Parser[Input, Input]):
    def __init__(self, parser: Parser[Input, Output]):
        super().__init__()
        self.parser = parser

    def consume(self, reader: Reader[Input]):
        status = self.parser.consume(reader)

        if isinstance(status, Continue):
            metadata = TrackingMetadata(
                reader.position,
                repr(self.parser),
                status
            )
            result = generate_subclass_with_attributes(
                status.value,
                'Tracked',
                TrackedValue,
                {'metadata': metadata}
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


tagged_subclass_cache = dict()

@dataclass
class TaggedValue:
    tag: Any


class TagParser(Generic[Input, Output], Parser[Input, Input]):
    def __init__(self, parser: Parser[Input, Output], tag:Any):
        super().__init__()
        self.parser = parser
        self.tag = tag

    def consume(self, reader: Reader[Input]):
        status = self.parser.consume(reader)
        if not isinstance(status, Continue):
            return status
        result_value = status.value
        result_value = generate_subclass_with_attributes(
            result_value,
            'Tagged',
            TaggedValue,
            {'tag': self.tag}
        )
        status.value = result_value
        return status

    def __repr__(self):
        return self.name_or_nothing() + 'label({})'.format(repr(self.parser))


def tag(parser: Parser[Input, Output], label:str) -> ExcludingParser:
    if isinstance(parser, str):
        parser = lit(parser)
    return TagParser(parser, label)