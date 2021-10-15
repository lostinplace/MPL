# Keyflags

## Warn
The Warn keyflag indicates that the interpreter will scan the provided policies for potential conflicting assignments.  If it is determined that a conflicting assignment could occur, a warning will be raised in the Policy evaluation stage but all assignments for this key will be treated as if it was set to `Allow`

## Allow and Reject
> We process the assignments in order of highest priority.  For assignments with conflicting priorities, we group the assignment by proposed value and calculate the relative weights of each assignment.  We use a random number to select the value to be assigned based on the weight associated with that value

Once a value from the list of assignments has been selected the Allow or Reject Strategies differentiate.

In the case of Allow:
> We assign the value, and return to all rules that their operation was accepted and they can continue processing

In the case of Reject:
> We assign the value then inform the selected rules that their operations were accepted, and that they can continue processing.  The rules that provided values that were not selected are informed that their assignment was rejected, and that they should discontinue further processing

Please note that all assignments have a default priority of 0 and weight of 1.0.

### Priority

Priority is a signed int8 value (-128 to 127) that determines the order that a collection of assignments should be executed in, from highest to lowest.  Take the following assignments for example:

```
a: INT  {Allow}

a = 1 {1, 1.0}
a += 2 {2, 0.5}
a = 5 {3}

Note: If a single number is provided in braces, integers are evaluated as priority with a default weight of 1.0
```

If these assignments were to be queued for execution at the end of a Machine's step, the resulting value would be `a==7`.  Since direct assignment using the equals `=` operator competes based on priority, It is evaluated first.  The assignment `a=5` gets  processed because it is highest priority, `a+=2` is next resulting in `a==7`.

### Weight

Weight is a double value between 0.0 and 1.0 that determines the likelihood that if a random number was sampled its value would cause the associated assignment to be executed.

For example:
```
a: {Allow}

a += 1 {0, 0.5}
a += 2 {0, 0.3}
a += 2 {0, 0.25}
a += 5 {0.1}
a = 2 {1}

Note: If a single number is provided in braces, decimal values between 1 and 0 are evaluated as weight with a default priority of 0
```

From the above example, it is clear that we have several conflicting assignments to the context key `a`.  When these assignments are evaluated, they will be ordered by priority, then grouped by value, and selected based on a draw of a random number.  Specifically, this evaluation will produce:

```
total: 0.5 + 0.3 + 0.1 + 0.25 = 1.15

a=2

a += 1 {0.5/total = 0.434)
a -= 2 {0.55/total = 0.47)
a += 5 {0.1/total = 0.086) 
```

First, `a` is assigned the value 2, since the last rule had a priority of 1 which is higher than all of the others at 0

Next, a random number is drawn, and if its proportion to the max random value is lower than the smallest calculated weight, (in this case 0.086) then it is selected, and `a` is increemented 5.  if it is between 0.086 and 0.52 (0.086 + 0.434) `a` is incremented by 1, and any other number will result in a decrement by 2, since it has the highest calculated weight: 0.47.

This means that the probability distribution of final values is:

```
0.086 : 7
0.434 : 3
0.47  : 0
```

## Resolve

The Resolve Keyflag indicates that any competing assignments will be returned to the host process before evaluation can continue.  The Host process will be provided all competing assignments with their associated priorities and weights, and it must return a return a value in order for operations to continue.

The host function must register a handler for the engine with the following prototype:

```
(Machine, List[Assignment]): (Value, KeyFlag: Allow|Reject) 
```

When the returned value is provided, the provided Keyflag will be used to determine how the rules that raised the conflicting assignments should proceed.

If no resolver is provided by the host process, the `Reject` behavior will be assumed by default.

## Deny

The Deny keyflag indicates that a state machine may not issue any changes to the flagged key.  If it is determined that any assignment to the specified key could occur, an error will be raised in the Policy evaluation stage and evaluation/generation will be halted.