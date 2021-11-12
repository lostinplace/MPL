from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Sequence, Union
from parsita import Parser, lit, TextParsers
from parsita.state import Input, Output, Continue, Reader
from Parser.ExpressionParsers.rule_expression_parser import RuleExpression
from lib.additive_parsers import TrackedValue
from lib.repsep2 import SeparatedList


@dataclass(frozen=True, order=True)
class DefinitionTreeNode:
    definition_expression: RuleExpression | TrackedValue
    parent: DefinitionTreeNode
    children: RuleExpression | 'DefinitionTreeNode'


class TreeConversionParser(Generic[Input, Output], Parser[Input, Sequence[Output]]):
    def __init__(self, parser: Parser[Input, Output]):
        super().__init__()
        self.parser = parser

    def consume(self, reader: Reader[Input]):
        status = self.parser.consume(reader)
        if not isinstance(status, Continue):
            return status

        output = []
        current_depth = 0
        current_node = None

        result: TrackedValue
        status.value: SeparatedList

        for result in status.value:
            if not isinstance(result, TrackedValue):
                continue
            this_line_depth = result.metadata.start

            if this_line_depth == 0:
                if current_node:
                    while current_node.parent is not None:
                        current_node = current_node.parent
                    output.append(current_node)
                this_node = DefinitionTreeNode(result, None, [])
            elif this_line_depth > current_depth:
                this_node = DefinitionTreeNode(result, current_node, [])
                current_node.children.append(this_node)
            elif this_line_depth == current_depth:
                this_node = DefinitionTreeNode(result, current_node.parent, [])
                this_node.parent.children.append(this_node)
            elif this_line_depth < current_depth:
                while current_node.definition_expression.metadata.start > this_line_depth:
                    current_node = current_node.parent
                this_node = DefinitionTreeNode(result, current_node.parent, [])
                this_node.parent.children.append(this_node)
            current_node = this_node
            current_depth = this_line_depth

        while current_node.parent is not None:
            current_node = current_node.parent

        output = output + [current_node]
        status.value = output
        return status

    def __repr__(self):
        return self.name_or_nothing() + f"tree({repr(self.parser)})"


def tree(
    parser: Union[Parser]) -> TreeConversionParser:
    if isinstance(parser, str):
        parser = lit(parser)
    return TreeConversionParser(parser)