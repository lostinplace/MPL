from Tests import quick_parse
from mpl.Parser.ExpressionParsers.machine_expression_parser import MachineFile
from mpl.Parser.ExpressionParsers.reference_expression_parser import ReferenceExpression


def test_mpl_file_parser_doesnt_fail():
    result = MachineFile.from_file('Tests/test_files/simple_wumpus.mpl')

    assert result


def test_parsing_with_context():
    actual = MachineFile.from_file('Tests/test_files/simplest.mpl')

    expected_context = {
        quick_parse(ReferenceExpression, 'One'): frozenset([1]),
        quick_parse(ReferenceExpression, 'Two'): frozenset([2]),
        quick_parse(ReferenceExpression, 'Three'): frozenset([3]),
    }

    assert actual.context == expected_context
