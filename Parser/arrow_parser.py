from dataclasses import dataclass
from typing import Optional

from parsita import TextParsers, lit


@dataclass(frozen=True, order=True)
class Arrow:
    left: Optional[str]
    middle: str
    right: str

def process_arrow(results):
    if len(results) == 2:
        results = [None] + results
    return Arrow(results[0], results[1], results[2])


class ArrowParser(TextParsers):
    event_indicator = lit('*')
    transition_indicator = lit('>')
    connector = lit('-')

    simple_transition_arrow = connector & (event_indicator | transition_indicator)

    complex_transition_arrow = \
        (event_indicator & connector & (transition_indicator | event_indicator)) | \
        ((event_indicator | connector) & transition_indicator & (transition_indicator | event_indicator))

    arrow = (simple_transition_arrow | complex_transition_arrow) > process_arrow