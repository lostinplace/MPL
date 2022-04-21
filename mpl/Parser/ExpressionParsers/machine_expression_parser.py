from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Optional, FrozenSet

from parsita import TextParsers, reg, longest, Success, lit, opt, rep
from parsita.util import splat

from mpl.Parser.ExpressionParsers.reference_expression_parser import ReferenceExpression, \
    ReferenceExpressionParsers as RefExP
from mpl.Parser.ExpressionParsers.rule_expression_parser import RuleExpression, RuleExpressionParsers as RuleExP
from mpl.Parser.ExpressionParsers.query_expression_parser import VectorExpression, VectorExpressionParsers

from mpl.lib.parsers.additive_parsers import track, TrackedValue
from mpl.lib.parsers.custom_parsers import check
from mpl.lib.parsers.repsep2 import repsep2, SeparatedList


@dataclass(frozen=True, order=True)
class BlankLine:
    pass

    @staticmethod
    def interpret(*_) -> BlankLine:
        return BlankLine()


@dataclass(frozen=True, order=True)
class MachineFile:
    lines: SeparatedList[ReferenceExpression | RuleExpression | TrackedValue]
    context: Optional[Dict[ReferenceExpression, FrozenSet]] = None

    @staticmethod
    def parse(text: str) -> MachineFile:
        result = MachineDefinitionExpressionParsers.machine_file.parse(text)
        assert isinstance(result, Success)
        return result.value

    @staticmethod
    def from_file(path: str) -> MachineFile:
        with open(path, 'r') as f:
            content = f.read()
            return MachineFile.parse(content)

    @staticmethod
    def interpret(
            lines: SeparatedList[ReferenceExpression | RuleExpression | TrackedValue],
            context: List[str]
    ) -> MachineFile:

        if context:
            context_items = []
            for item in context[0]:
                context_items.append(tuple(item))

            return MachineFile(lines, dict(context_items))
        return MachineFile(lines)


class MachineDefinitionExpressionParsers(TextParsers, whitespace=None):
    ignored_whitespace = reg(r"[ \t]*")
    iw = ignored_whitespace

    rule_line = iw >> track(RuleExP.expression) << iw
    declaration_line = iw >> track(RefExP.expression) << iw
    empty_line = iw << check('\n') > BlankLine.interpret
    valid_line = longest(empty_line, declaration_line, rule_line)
    rule_lines = repsep2(valid_line, '\n', reset=True, min=1)
    context_line = RefExP.expression << ':' & VectorExpressionParsers.expression_as_frozen_set
    context_lines = repsep2(context_line, '\n', reset=True, min=1)
    divider = lit('---\n')
    machine_file = rule_lines & opt(divider >> context_lines) << opt(rep(empty_line)) > splat(MachineFile.interpret)

