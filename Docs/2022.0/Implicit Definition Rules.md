# Implicit Definition Rules

The following rules are used in priority order to determine the types of symbols that are referred to in an MPL Policy:

0. All implicit definition rules are assessed as independent passes of a policy, in order from top to bottom of the policy.
1. Any shorthand (e.g. exclusive substates) is evaluated before implicit definitions
2. Any explicit definition automatically takes precedence over implicit definitions, and is evaluated after shorthand
3. Any undefined symbols in a **State Expression** to the left of a `->` or `~>` will be defined as a `STATE` with default flags.
4. Any undefined symbols in a **State Expression** to the left of a `*->` or `*~>` will be defined as a `TRIGGER` with default flags.
0. Any undefined symbols with attached parens (e.g.  MyFunc(a) ) will be defined as `CONTEXT` with a type flag `FUNC` with interior type flags being correlated appropriately
   1. Competing value types will cause an error at policy evaluation time
0. Any Symbol in an **Assignment Expression** will be defined as `CONTEXT` with a type flag correlated with the value being assigned.
   1. Competing value types will cause an error at policy evaluation time
0. Any undefined symbols in a **Condition Expression** will be defined as `CONTEXT` with a type flag correlated with the value being compared.
   1. Competing value types will cause an error at policy evaluation time

 