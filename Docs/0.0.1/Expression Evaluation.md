# Expression Evaluation

This details the procedures for evaluating rules and expressions.

## State Transistion Expression

### AND

` a & b -> c `

if a ∧ b , then δ ≝ a ∪ b, after the rule is executed, δ ⊆ c , a=∅, b=∅

### OR

`a | b -> c`

if a ∪ b ≠ ∅, then δ ≝ a ∪ b, after the rule is executed, δ ⊆ c, a=∅, b=∅

### XOR

`a ^ b -> c`

if a ⊻ b, then δ ≝ a ∪ b

after the rule is executed: δ ⊆ c, a=∅, b=∅

### NOT

#### Example 1

```mpl
* -@ x = y + 2
* -@ a = 0

!a & x -> c

```

given δ ≝ {¬a, x} ≣ { ⊨ , y+2 } ≣ { y+2 }

after the rule is executed

δ ⊆ c, a ≣ ∅, x ≣ ∅

#### Example 2

```mpl
* -@ x = y + 2
* -@ a = 1

!a | x -> c

```

given δ ≝ {¬a, x} ≣ { ⊭ , y+2 } ≣ { y+2 }

after the rule is executed

δ ⊆ c, a ≣ 1, x ≣ ∅

#### Example 3

```mpl
* -@ x = y + 2
* -@ a = 1

a | x -> c & !d

```

given d ≣ ∅, δ ≝ {a, x} ≣ {1, y+2 }

after the rule is executed

δ ⊆ c, a ≣ ∅, x ≣ ∅, d ≣ ∅

the moment you usee thee entity in an expression, it becomes a logical value, not an entity reference



### Arithmetic expression

```mpl
* -@ x = 1
* -@ a = y + 1

x - 1 | a -> c

```

given δ ≝ {x-1, y+1} ≣ {1-1, y+1}  ≣ { y + 1 }

after the rule is executed

δ ⊆ c, a = ∅, x = 1


---
## Arithmetic Expressions

### Example

```mpl
1+(test-3)*4
```

### Definition

```python
def evaluate_expression(expression: 'ArithmeticExpression', reference_cache: 'Dict'['Reference', 'Number' | str | 'MPLEntity']) -> 'Number':
    ...
```

This is the most straightforward, we convert the expression to postfix notation beefore evaluation.  The cache is used as the source of values, and only numeric values are supported at this time.

The result  of any ArithmeticExpression is a Number

## Scenario Expression

```mpl
%{ 5 + (test/5) ^ 2}
```

### Definition

```python
def evaluate_expression(expression: 'ScenarioExpression', reference_cache: 'Dict'['Reference', 'Number' | str | 'MPLEntity']) -> 'ScenarioDescriptor':
    ...
```

The arithmetic expression within the `%{}` determines the scenario's weight. Scenarios can be consumed or obseerved.

given 3 scenarios:
```mpl
* -@ a = `ok`

a -> %{2} -> b
a -> %{3} -> c
a -> %{4} ~> d
```


|                  Outcome                   |  P  |
|:------------------------------------------:|:---:|
|     not (a or c or d) and b is `ok`        | 2/9 |
|      not (a or b or d) and c is `ok`       | 3/9 |
| not (a or b or c) and d is (`ok` and True) | 4/9 |


this is because the scenario `c` doesn't continue the chain of consumption that originated with `a`.  The observation of scenario denoted `%{4}` is passed directly to `d`.  Compare that with the following:

```mpl
* -@ a = `ok`

a -> %{2} -> b
a -> %{3} -> c
a -> %{4} ~> 10 -> d
```

|                  Outcome                   |  P  |
|:------------------------------------------:|:---:|
|      not (a or c or d) and b is `ok`       | 2/9 |
|      not (a or b or d) and c is `ok`       | 3/9 |
| not (a or b or c) and d is (`ok` and `10`) | 4/9 |


Note that the state of the observation collapses when provided with more information, in this case the result of the arithmetic operation `10`.


## Target Expressions

The last expression in a rule defines a target for the results of all  prior expreessions.  Targets are assessed differently.

1. A Reference is not a valid target if it is used in an arithmetic expression
2. Generally logical expressions operate on the principle that the tarrget expression must be true after the assignmeent of results to the targets, logic is described below.


### AND

` a -> b & c `

if a then δ ≝ a

after the rule is executed, δ ⊆ a, δ ⊆ a, a=∅

### OR

`a -> c | d`

if a then δ ≝ a 

after the rule is executed, 

δ ⊆ c ∪ d such that if !c then !c and if !d then !d
a=∅

### XOR

`a -> c ^ d`

if a and c ⊻ d then δ ≝ a

after the rule is executed: 
δ ⊆ c ⊻ d such that if !c then !c and if !d then !d
a=∅




