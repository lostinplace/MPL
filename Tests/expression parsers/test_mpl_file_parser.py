from parsita import Success

from Parser.ExpressionParsers.machine_expression_parser import MachineDefinitionExpressionParsers as MDExP


def test_mpl_file_parser():
    with open('Tests/test_files/simple_wumpus.mpl') as f:
        content = f.read()

    result = MDExP.machine_file.parse(content)

    assert isinstance(result, Success)
