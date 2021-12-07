from dataclasses import dataclass
from numbers import Number
from typing import Dict

from Parser.ExpressionParsers.reference_expression_parser import Reference
from Parser.ExpressionParsers.scenario_expression_parser import ScenarioExpression
from interpreter.reference_resolution.reference_graph_resolution import MPLEntity


@dataclass(frozen=True, order=True)
class ScenarioDescriptor:
    weight: Number


def evaluate_expression(
        expression: ScenarioExpression,
        reference_cache: Dict[Reference, Number | str | MPLEntity]
) -> Number:
    import arithmetic_expression_interpreter as ArExI

    return ScenarioDescriptor(ArExI.evaluate_expression(expression, reference_cache))

