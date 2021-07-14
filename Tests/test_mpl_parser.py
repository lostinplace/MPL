from dataclasses import dataclass

from parsita import Success, Parser

from Parser.expression_parser import ExpressionParsers, Any, Label
from Parser.mpl_parser import process_declaration
from Parser.mpl_parser_classes import Declaration, Event, State, default_state, Rule


def eval_match(parser, statement, expectation):
    result = parser.parse(statement)
    expected = Success(expectation)
    assert result == expected


def eval_matches(parser, expectations):
    for expectation in expectations:
        eval_match(parser, expectation[0], expectation[1])


def test_parse_declaration():
    samples = [
        ("test_ent", "ENTITY", Declaration(Entity("test_ent"))),
        ("test_event", "Event", Declaration(State("test_event", default_state("Event"), True)))
    ]

    for sample in samples:
        result = process_declaration(sample[0], sample[1])
        assert result == sample[2]


def test_expression_parser():
    expressions = [
        "1+1",
        "1^12+1",
        "1^12-1+15",
        "12*34+56",
        "(12*34+56)",
        "(12*34+56)+1",
        "1+(2*(3-4/5)+56)-1",
        "1 + ( 2 *(3-4 / 5)+56)-1",
        "alfred",
        "alfred - (bruce & jack)",
    ]

    results = [ExpressionParsers.expression.parse(_) for _ in expressions]

    for result in results:
        assert isinstance(result, Success)


def test_assignment_parser():
    expressions = [
        "test = 1+1",
        "test2 += 1",
        "test3&=froyo",
        "test4 |= alfred - (bruce + -2) * 3",
    ]

    for expression in expressions:
        result = ExpressionParsers.assignment.parse(expression)
        assert isinstance(result, Success)
    pass


@dataclass(frozen=True, order=True)
class E:
    expression: str
    parser:  Parser
    expectation: Any


@dataclass(frozen=True, order=True)
class Result:
    value: Any
    expectation: Any


def test_basic_mpl_parsing():
    from Parser.mpl_parser import MPLParser as M
    from Parser.mpl_parser_classes import Transition as TRANS, TransitionType as TT, Trigger as TRIG

    expressions = [
        E("foo:STATE", M.declaration, Declaration(default_state('foo'))),
        E("foo:bar", M.declaration, Declaration(State(Label('foo'), default_state('bar'), True ))),
        E(
            "Foo -> Bar",
            M.rule,
            Rule(
                [
                    TRANS(Label('Foo'), Label('Bar'), TT.HARD)
                ]
            )
        ),
        E(
            "Foo *-> Bar",
            M.rule,
            Rule(
                [
                    TRIG(Label('Foo'), Label('Bar'), TT.HARD)
                ]
            )
        )
    ]

    results = [Result(_.parser.parse(_.expression), _.expectation) for _ in expressions]

    for result in results:
        assert isinstance(result.value, Success)
        assert result.value == Success(result.expectation)

