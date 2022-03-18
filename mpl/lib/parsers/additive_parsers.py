from dataclasses import dataclass, is_dataclass
from typing import Any, Generic, Dict, Tuple, Callable

from parsita import Parser, Reader, lit
from parsita.state import Input, Output, Continue

from mpl.lib.parsers.custom_parsers import ExcludingParser


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
    source: str
    tag: Any


class TrackedValue:
    metadata: TrackingMetadata


class TrackParser(Generic[Input, Output], Parser[Input, Input]):
    tag: Any

    def __init__(self, parser: Parser[Input, Output], tag: Callable[[Any], Any] = None):
        super().__init__()
        self.parser = parser
        self.tag = tag


    def consume(self, reader: Reader[Input]):
        status = self.parser.consume(reader)

        if isinstance(status, Continue):
            if isinstance(self.tag, Callable):
                tag_value: Any = self.tag(status.value)
            else:
                tag_value = self.tag


            if status.remainder.finished:
                final_position = None
            else:
                final_position = status.remainder.position

            metadata = TrackingMetadata(
                reader.position,
                repr(self.parser),
                reader.source[reader.position:final_position],
                tag_value,
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


def track(parser: Parser[Input, Output], tag:Any=None) -> TrackParser:
    """Tracks metadata about the result of the provided parser

    Args:
        :param parser: a parser that parses terms that you want to make sure are present
    """
    if isinstance(parser, str):
        parser = lit(parser)
    return TrackParser(parser, tag)