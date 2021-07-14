# Expressions

### State Expressions

A state expression is a logical expression that combines symbols to produce an assertion about the state of a machine.  These state expressions are themselves treated as atomic states even though they are comprised of states and triggers.  

#### Operators
`&` `|` `!`

#### Operands

STATE, TRIGGER

#### Example

Consider the following Machine definition:

```mpl
Furnace: MACHINE
  Overheating: STATE
  Override: STATE
  Kill Signal: TRIGGER
  Off: STATE
```

given the following **State Expression**

`Overheating & !Override | Kill Signal`

This expression can be evaluated as:
> While Overheating is active and Override is not active or the Kill Signal is present

With this, we can imagine the following transition rule:

```
Overheating & !Override | Kill Signal -> Off
```

In this example, the state expression is treated as an atomic state.  When it evaluates positively, a transition will occur that activates the `Off` state.

In this example the state, `Overheating` will be deactivated if it was previously active and Override was not.  In this event however, the activation state of `Override` will not be changed at all, since it was not evaluated through a direct reference.  (This implies that any direct reference can be protected from deactivation using the `!!` notation, such as `!!Overheating`)

Note that this state expression includes a reference to a trigger to the left hand side of the `->` operator.  State expressions can include references to both Triggers and States, but the right-hand operator is important.  The `->` will cause execution of the rule to occur whenever any of the states are active, but the `*->` operator will only cause execution to occur when all of the triggers in the expression are present.

### Function Expressions

Function expressions are a type of expression that calls a function provided by the context with arguments available to the machine at step time.  The value returned by the function is made available to the interpreter.

Please note that by default, function evaluations are cached (unless they are the sole component of an action state), meaning that calling them with the same arguments will produce the same result, even if the host systems execution of the function has changed, to override this use the NO-CACHE flag.

#### Operators

`()`

#### Operands

LHS: CONTEXT(FUNC) 

RHS: [ANY]

#### Flags

CACHE, NO-CACHE

#### Examples

```
A(B)

FetchFromInternet("ID", url) {NO-CACHE}
```


### Arithmetic Expressions

Arithmetic Expressions perform basic arithmetic using provided symbols and values.

#### Operators

`+` `-` `*` `/` `^` `()`

#### Operands

CONTEXT(INT|DOUBLE), Values, Arithmetic Expressions

#### Example

```
a + 1
```

```
2 * 3 / (X+Y)
```

### Comparison Expressions

Comparison expressions are a type of expression that evaluates a statement as either True or False based on the relative values of the operands.

#### Operators

`==` `!=` `>` `>=` `<` `<=`

#### Operands

CONTEXT(ANY), Values(NUMERIC and STRING), Arithmetic Expressions

#### Example

```
A == X+1 * (B*15)

B == True

Fuel == 0.0
```

### Logical Expressions

Logical expressions are a type of expression that evaluates a statement as either True or False

#### Operators

`&&` `||` `!`

#### Operands

CONTEXT(BOOL), State Expression, Comparison Expressions, Logical Expressions

#### Examples

```
A && B

A && (B || C) || !D

Noisy && (Stopped && Off && Quiet) || Fuel == 0 
```



### Assignment Expressions

Assignment expressions are a type of expression that assigns the value of the right hand operand to the context key indicated by the left hand operand.

#### Operators

`=` `+=` `-=` `*=` `|=` `&=` `~=`

#### Operands

LHS: CONTEXT(ANY)

RHS: CONTEXT(ANY), Arithmetic Expression, Logical Expression, Comparison Expression, State Expression, Function Expression

#### Examples

```
A = 1

Fuel += 10

Efficiency *= Loss / Rate +1

Needs Repair = (Broken | Noisy) || (Faults > 0) 

External Value = FetchFromInternet("ID", url) {1, 0.5}
```
