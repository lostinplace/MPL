# Reference Resolution Rules (Q3 2021)

1. All names must be unique by type
2. a reference usage of a different type spawns a separate reference of the used type.  This is insecure, because it means that refernces can be secretly multi-purposed.  Not only should this be ledgered, but refernces should be lockable
3. all triggers exist in a global space with a reference to the source of the trigger.


## MPL Graph Rules

vertices

`MPLLine(line number, depth, str)`:  This describes a line from the MPL File

`Reference(name, None)`  
`Reference(name, type)`  : These are createed for every reference, right now we're not dealing with pathed references, but eventually the second option will be replace d with a fully patheed version

`MPLRule(id, clauses, operators)`:  this is tracked for every rule discovered

`MPLClause(id, expression)`:  this is tracked for every clause discovered

`MPLEntity(name, entity_class, value_type, value)`:  This is tracked vor every discovered machine


edges:

1. Defined By:  This is a relation to a line artifact from the defining file, it describes the position, offset and text of the line 
2. Qualified by:  this links aliases to their fully-qualified references
3. Child of:  This links clauses to rules, rules to states and machines and states and machines to their parents.
4. Exclusive Child Of: This links states to their parent states
5. Evaluated in:  This links references to the clauses that evaluate them
6. Changed in:  this links references to the clauses that change them:
7. Instantiated as:  this links references to their instantiated types

## Assignment

for states, transitioning or assigning a value to that state will add the value to that state.  values can only be drained by transitioning them to other states (including void).  comparison for those states will be treated as, `all`

for variables, assignment will overwrite the value, and transitions will `copy` the value and pass it along


## Void operations

Entry from the void is processed whenever initialization occurs.  The only rules evaluated during this stage are the "Entry from the void" rules.  

## Variable alteration

Variable alteration will only occur in the event of an assignment expression.  Consuming the value of any expression simply means, "Pass this value to the next valid recipient"

### Examples:

```mpl

foo:state
bar:state
caz:string
dax:int

* -@ foo = 1
* -@ bar = `test`

foo -> dax
`this will do nothing because dax is not a valid recipient of foo's state (dax is a variable that can only be altered by assignment expressions)`

foo -@ dax
`this will reesult in dax being altered, and foo inactive`

foo -> bar -@ dax
`this will never fire because there is no valid recipient for bar's value`

foo -> bar -@ dax -@ caz
`this will result in dax=1, and caz = "test", foo and bar inactive`

fan:state
* -@ fan= 5

foo -> fan -> bar -@  caz -> *
`this will result in caz = "test", foo and bar inactive`, * is a valid recipient for anything

```

## Valid recipient

Valid recipients are the right-most state expressions in a rule.  Their logic is processed a bit differently.  Firstly, in order to be a valid recipient, the expression must evaluate to `True` or `unassigned`.

### Examples

```mpl
foo -> bar & caz
```

the value of `foo` is consumed and assigned to both `bar` and `caz`.  this will evaluate to True as long as both bar and caz are valid targets

```mpl
foo -> bar | caz
```

the value of `foo` is consumed and assigned to either bar or caz depending on which is a valid recipient.  if both are valid recipients, then 1 will be selected with a P(1/2)


```mpl
foo -> bar & !bar
```

this will consume `foo` and assign it to `bar` only when `bar` is not assigned.  note that `!bar` represents a valid recipient, but the destination of the data is ultimately the same as `*` (void)


## Observation vs. consumption

Consuming a state drains the value of that state, and passes the value along to the next valid recipient in the expression.  If no valid recipients exist, then the expresssion is not a possible outcome.

Consuming a value passes that value along to the next available recipient

Observing a state means to evaluate whether it has been assigned any value.  Observing a value means to evaluate whether or not it is "truthy", and continue if they are.  observations are low-priority values, meaning they'll be assigned only if no other value is eligible for the recipient 

### Examples:

#### Simple

```mpl

foo:state
bar:state
baz:state

* -@ foo = 1

foo ~> bar
foo -> baz

```

In this example, there is no competition between the 2 mutative rules that rely on foo, `bar` will be assigned `true` and `baz` will be assigned `1`. `foo` will be left inactive

#### Slightly more complex

```mpl

a:state
b:state
c:state
d:state

* -@ a = 1
* -@ b = 2

a -> b ~> c
a ~> b -> d

```

again, in this example, there is no competition, c will be set to 1, and d will be set to 2.

## Probabilistic Evaluation

Since all rules are evaluated in parallel, there will be situations when 2 rules produce conflicting outcomes.  These conflicts are handled probabilistically, meaning the consequences of competing rules are selected randomly before being committed.

### Examples

```mpl

foo: int

foo = 1
foo = 2
foo *= 3

```

When this machine is evaluated, there are three possible outcomes on every tick.  within the documentation the probability of an outcome is noted as `(r,C) = P` given:
* `r` is the specific resource under contention
* `C` is the condition under evaluation   
* `P` is the Probability oof the outcome

* An example is presented here:

| Condition         | Probability | action  |           explanation      |
|:-----------------:|:-----------:|:-------:|:--------------------------:|
| (`foo`, unassigned) | 1/2         | `foo = 1` | there are two other outcomes for `foo`, but one is invalid |
| (`foo`, unassigned) | 1/2         | `foo = 2` | there are two other outcomes for `foo`, but one is invalid |
| (`foo`, unassigned) | 0           | `foo *= 3`| since `foo` has not been assigned, it cannot be incremented here|
| (`foo`, assigned)   | 1/3         | `foo = 1` | |
| (`foo`, assigned)   | 1/3         | `foo = 2` | |
| (`foo`, assigned)   | 1/3         | `foo *= 3`| |
 
 
if you want to adjust the probability of an outcome, you can load present it as a `Scenario Expression` using the `%{}` operator which provides other pathways to get to the outcome.  For example:


```mpl

foo: int

foo = 1
%{10} -@ foo = 2
foo = 3

```

| Condition | Probability | action           |           explanation      |
|:---------:|:-----------:|:----------------:|:--------------------------:|
| (`foo`, )   | 1/12        | `foo = 1`          | |
| (`foo`, )   | 10/12       | `%{10} -@ foo = 2` | scenario operator added a weight of 10 to the distribution |
| (`foo`, )   | 1/12        | `foo = 3 `         | |



## Order of Operations

clauses are processed in-order left-to-right.  Assignment expressions are the only thing that requirees sequentiality, as evaluations to the left must be preformed before an assignment is completed, and evaluations to the right may be performed after the assignment.  Single-reference assignment expressions will probabilistically aggregate changes up until that point into a variable, but state's values will continue on.

### Example

```mpl

foo: state
bar: int
caz: int
dax: state

caz = 10
caz = -10

foo = 1
foo = -1
foo -@ bar -> bar > 0 ~@ bar *= caz -> bar < 0 -> dax

 


```

this one is complicated, but let's break it down.

right off the bat, we have resource contention for `foo`, it can be altered in 3 separate rules, each with a P(1/3).

within the rule, `foo -@ bar -> bar > 0 ~@ bar *= caz -> dax` we have a few clauses:
1. if foo is assigned, pass its value, de-assigning foo
2. assign the value of foo to `bar`. 
3. if bar > 0 then continue. note that there's a P(1/2) of this condition since it can either be 1 or -1
4. increment multiply bar and caz, which is either 10 or -10 with a P(1/2)
5. if `bar` was 1 before, and it was multipled by -10, it's now less than 0, so we should continue, note that this has a P(1/4), which is the product of the P in clauses 3 and 4
6. we assign the value -10 to `dax`

from this you can see that the first 1/4 of ticks of this machine will result in:
```
!foo
dax == 10
```

in other remaining first 3/4 ticks:
```
foo == 1 || foo == -1
!dax
```

as the system continues, the probability that dax is never assigned goes down dramatically, meaning that the most likely of P((n-1) / n) where n is the number of ticks elapsed:

```
foo == 1 || foo == -1
dax == 10
```







## Value Passing

[//]: # (TODO: this needs work)



`a->b->c` a and b are consumed, c is assigned the values of a and b
`a->b~>c` a is consumed and b is observed. c is assigned the value of a and observation of b
`a~>b->c` a is observed and b is consumed. c is assigned the observation of a and value of b
`a~>b~>c` c is assigned the observation of a and b.  both a and b must be true

`a->b<10~>c->d-@ e=7` as long a b < 10, the values of a and c are consumed and assigned to d. if this is successful, e is assigned the value 7

after consuming a, as long as b is less than 10 and after a is assigned to c, 


consumptions all target the last eligible target in the rule.  this means that the last state, or the last assignment to a value with an compatible type

### Example

```mpl

a:state
b:state
s:string
i:integer
s2:string

a = `test`
a -> i
a -> b
a -> s
a -@ s
s = `ack`
a -> s -> s2
a -> s -@ s2
```

if a is empty, then it will be set to test
if a is not empty, then:

|   p               |   action            |           explanation      |
|:-----------------:|:-------------------:|:--------------------------:|
| 1/4 {a}           |  ``` a=`test` ```   | a is assigned the value `test`|
|  0  {a}           |  `a -> i`           | i is not a valid recipient of the state a|
| 1/4 {a}           |  `a -> b`           | a is left empty, and b is assigned `test` |
| 0                 |  `a -> s`           | s is not a valid recipient of the state a|
| 1/4 {a} * 1/3 {s} |  `a -@ s`           | a is left empty, and s is set to `test`|
| 1/3 {s}           |  ``` s = `ack` ```  | s is assigned the value `ack`  |
| 0                 |  `a -> s -> s2`     | this is invalid because there are no valid recipients for the state a|
| 1/3 {s}           |  `a -> s -@ s2`     | s is assigned the value `test` because it is a valid recipient of a's state  |








[//]: # (TODO: states should have distributions of values, not just single ones)
[//]: # (TODO: assignment expressions can stand alone)
[//]: # (TODO: assignment expressions can be just a single reference)

`a->b` will result in the consumption of `test` and assignment to the state b,
`a->s` will result in the consumption of `test` and assignment to the variable s,
`a->i` will never be true





## Blocking

[//]: # (TODO: this needs work)

```mpl
{*} -> a ~> any -| a
{*} -> a -> any -| a
{*} -> a -> any ~| a
{*} -> a ~> any ~| a
c -> a
```

in this scenario, a cannot transition to c while b is true.  these two statements compete, meaning that there is a p=0.5 that if b and a are true, a will transition to c 

assignments and comparisons and evaluatoins are performed in-order, while consumption is is evaluated in parallel

all consumptions are directed to the last possible target for consumption in the list
