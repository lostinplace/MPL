from Parser.ExpressionParsers.assignment_expression_parser import AssignmentExpression
from Parser.ExpressionParsers.reference_expression_parser import Reference
from Parser.ExpressionParsers.rule_expression_parser import RuleClause, RuleExpression
from Parser.ExpressionParsers.state_expression_parser import StateExpression
from Tests import quick_parse
from interpreter.reference_resolution.reference_graph_resolution import ResolverGraphEdgeTypes, \
    expression_clause_to_refgraph, action_clause_to_refgraph, rule_expression_to_usegraph
from lib.simple_graph import SimpleGraph


def test_simple_state_clause_graph_construction():
    rge = ResolverGraphEdgeTypes
    expr = quick_parse(StateExpression, 'a & b & !c')
    clause = RuleClause('query', expr)

    expected_verts = {
        Reference('a', None),
        Reference('b', None),
        Reference('c', None),
        clause
    }

    expected_edges = {
        (Reference('a', None), rge.EVALUATED_IN, clause),
        (Reference('b', None), rge.EVALUATED_IN, clause),
        (Reference('c', None), rge.EVALUATED_IN, clause),
    }

    actual = expression_clause_to_refgraph(clause)

    assert actual.vertices == expected_verts
    assert actual.edges == expected_edges


def test_simple_action_clause_graph_construction():
    rge = ResolverGraphEdgeTypes
    expr = quick_parse(AssignmentExpression, 'a += b - c + (d-12)')
    clause = RuleClause('action', expr)

    expected_verts = {
        Reference('a', None),
        Reference('b', None),
        Reference('c', None),
        Reference('d', None),
        clause
    }

    expected_edges = {
        (Reference('a', None), rge.ASSIGNED_IN, clause),
        (Reference('b', None), rge.EVALUATED_IN, clause),
        (Reference('c', None), rge.EVALUATED_IN, clause),
        (Reference('d', None), rge.EVALUATED_IN, clause),
    }

    actual = action_clause_to_refgraph(clause)

    assert actual.vertices == expected_verts
    assert actual.edges == expected_edges


def test_rule_expression_graph_construction():
    rge = ResolverGraphEdgeTypes
    expr: RuleExpression = quick_parse(RuleExpression, 'Hurt ~> Feel Secure -> %{10} -> Feel Secure')

    expected_graph = SimpleGraph(
        {
            expr,
            Reference('Hurt', None),
            expr.clauses[0],
            Reference('Feel Secure', None),
            expr.clauses[1],
            expr.clauses[2],
            expr.clauses[3],
        },
        {
            (expr.clauses[2], rge.CHILD_OF, expr),
            (Reference('Feel Secure', None), rge.CONSUMED_IN, expr),

            (expr.clauses[0], rge.CHILD_OF, expr),
            (expr.clauses[1], rge.CHILD_OF, expr),
            (Reference('Feel Secure', None), rge.EVALUATED_IN, expr.clauses[1]),

            (Reference('Hurt', None), rge.EVALUATED_IN, expr.clauses[0]),

        }
    )

    actual_graph: SimpleGraph = rule_expression_to_usegraph(expr)

    assert expected_graph == actual_graph


# TODO: usegraph construction for entire machine file
