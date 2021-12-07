## Arithmetic Expressions

### Example

```mpl
1+(test-3)*4
```

### Definition

```python
def evaluate_expression(expression: ArithmeticExpression, reference_cache: Dict[Reference, Number | str | MPLEntity]) -> Number:
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
def evaluate_expression(expression: ScenarioExpression, reference_cache: Dict[Reference, Number | str | MPLEntity]) -> ScenarioDescriptor:
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
