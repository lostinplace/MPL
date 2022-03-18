from mpl.Parser.ExpressionParsers.machine_expression_parser import MachineFile


def test_mpl_file_parser_doesnt_fail():
    result = MachineFile.from_file('Tests/test_files/simple_wumpus.mpl')

    assert result
