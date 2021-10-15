from dataclasses import dataclass

from parsita import *
from parsita.util import splat

from lib.CustomParsers import excluding, at_least, check, debug, best
from Parser.old.arrow_parser import ArrowParser

"""

# Expressions

NUMBER = r/^((?!-0?(\.0+)?(e|$))-?(0|[1-9]\d*)?(\.\d+)?(?<=\d)(e-?(0|[1-9]\d*))?|0x[0-9a-f]+)$/

Numeric_Expression(content:String)

RESERVED = r/^[A-Z]+$/

Reserved(content:String)

STRING = r/`([^`]|\\`)*`/

String_Expression(content:String)

LABEL = r/\w/ & NOT(OPERATOR or : or ,)+ OPT(:\w+) 

Label_Expression(content:String, type: String)

Index_Operand: U(Number, Label_Expression, String_Expression, Arithmetic_Expression)

INDEX_EXPRESSION= LABEL[Index_Operand] OPT(:\w+)

Index_Expression(label: Label_Expression, index: Index_Operand)

METHOD_INVOCATION = LABEL(repsep(Index_Operand, ",") ) OPT(:\w+)

Argument(value: Index_Operand)

Method_Invocation()

method

VARIABLE = [\w\s] until OPERATOR

Arithmetic_Operators: * / - + ^ % ()

ARITHMETIC_EXPRESSION = (NUMBER | VARIABLE | ARITHMETIC_EXPRESSION) Arithmetic_Operator (NUMBER | VARIABLE | ARITHMETIC_EXPRESSION)

Arithmetic_Operand:U(Number,Variable,ArithmeticExpression)

Arithmetic_Expression(Arithmetic_Operand, Arithmetic_Operand, Arithmetic_Operator)

EQUALITY_OPERATORS = == !=

LOGICAL_OPERATORS = && ||

EQUALITY_EXPRESSION = (NUMBER | VARIABLE | ARITHMETIC_EXPRESSION | EQUALITY_EXPRESSION) Logical_Operator (NUMBER | VARIABLE | ARITHMETIC_EXPRESSION | EQUALITY_EXPRESSION)

Equality_Operand:U(Number | Variable | Arithmetic_Expression | Equality_Expression)

Equality_Expression(Equality_Operand, Equality_Operand, Logical_Operator)

STATE_OPERATORS = AND OR

STATE_EXPRESSION = VARIABLE

LOGICAL_EXPRESSION =  VARIABLE


LOGICAL_EXPRESSION = AR

Produces

Variable = NOT  

"""



@dataclass()
class Label:
    name: str


@dataclass()
class Operand:
    value: str


@dataclass()
class ArithmeticOperation:
    operand: str
    operator: str


@dataclass()
class LogicalOperation:
    operand: str
    operator: str


@dataclass()
class NoOp:
    operand: str


@dataclass()
class Combine:
    operand: str
    operator: str


@dataclass()
class Compare:
    operand: str
    operator: str


@dataclass()
class Expression:
    operations: list


@dataclass()
class Assignment:
    reference: Label
    operator: str
    value: Expression


@dataclass()
class Any:
    pass


def get_operation_type(operator: str):
    if not operator:
        return NoOp

    if ExpressionParsers.arithmetic_operator.parse(operator):
        return ArithmeticOperation
    elif ExpressionParsers.logical_operator.parse(operator):
        return LogicalOperation
    elif ExpressionParsers.comparison_operator.parse(operator):
        return Compare
    elif ExpressionParsers.combination_operator.parse(operator):
        return Combine

    return NoOp


def interpret_operation(*args):
    dt = None

    def interpreter(operand, operator):
        if not operator:
            return operand
        result = dt(operand, operator[0])
        return result

    if len(args) == 1:
        dt = args[0]
        return interpreter
    elif args[1]:
        dt = get_operation_type(args[1][0])
        return interpreter(args[0], args[1])

    return args[0]


class ExpressionParsers(TextParsers):
    arithmetic_operator = lit("+", "-", '*', '/', '^')
    arith_assign_operator = arithmetic_operator & '='

    logical_operator = lit('&&', '||', '!')
    logical_assign_operator = lit('&=', '|=')

    comparison_operator = lit('==', '!=', '~=', '<', '>', '<=', '>=')

    combination_operator = lit('&', '|')

    assignment_operator = arith_assign_operator | logical_assign_operator | '='

    any_operator = arithmetic_operator | arith_assign_operator | \
        logical_operator | logical_assign_operator | \
        comparison_operator | combination_operator | '='

    number = reg(r'-?\d+(\.\d+)?(e-?\d+)?') > float
    label = excluding(ArrowParser.arrow | lit('(', ')', ':') | any_operator) > Label
    operand = number | label

    arithmetic_operation = operand & opt(arithmetic_operator) > splat(interpret_operation(ArithmeticOperation))
    logical_operation = operand & opt(logical_operator) > splat(interpret_operation(LogicalOperation))
    comparison_operation = operand & opt(comparison_operator) > splat(interpret_operation(Compare))
    combination_operation = label & opt(combination_operator) > splat(interpret_operation(Combine))

    simple_operation = best(arithmetic_operation | logical_operation | comparison_operation | combination_operation)

    simple_expression = rep1(simple_operation) > Expression
    parenthesised_simple_expression = '(' >> simple_expression << ')'

    complex_expression = fwd()
    parenthesised_complex_expression = '(' >> complex_expression << ')'
    complex_operation = check(operand | '(') >> \
        (parenthesised_simple_expression | parenthesised_complex_expression | complex_expression) & \
        opt(any_operator) > splat(interpret_operation)

    complex_expression.define(at_least(2, simple_operation | complex_operation) > Expression)

    expression = (operand << eof) | \
        complex_expression | \
        parenthesised_complex_expression | \
        parenthesised_simple_expression | \
        simple_expression

    assignment = debug(label & assignment_operator & expression) > splat(Assignment)
