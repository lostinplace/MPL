from parsita import Success

from mpl.Parser.ExpressionParsers.machine_expression_parser import MachineDefinitionExpressionParsers as MDExP


def test_tree_parser():
    with open('Tests/test_files/simple_file.mpl') as f:
        content = f.read()

    result = MDExP.machine_file.parse(content)

    assert isinstance(result, Success)
