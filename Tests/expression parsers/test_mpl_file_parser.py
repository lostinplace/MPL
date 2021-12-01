from parsita import Success

from Parser.ExpressionParsers.machine_expression_parser import MachineDefinitionExpressionParsers as MDExP, \
    parse_machine_file


def test_mpl_file_parser():
    result = parse_machine_file('Tests/test_files/simple_wumpus.mpl')

    assert result
