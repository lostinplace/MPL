# MPL Operators

## Transition Operators

### Anatomy

The general anatomy of a transition operator follows the following rules:

* An operation is defined by the operator on its left, unless it is the originating trigger for a rule in which case it is defined by the * on its right
* an asterisk `*` represents a trigger
* a hard-dash `-` represents a consuming transition
* a soft-dash `~` represents an "observing" or non-consuming transition
* an arrow `>` represents a conditional state or state expression
* an at-sign `@` represents an action state
* a pipe `|` on the left is used to indicate a fork state


### Examples

```mpl

a *-> b
// The trigger a causes the activation of b

a -> b == 2 -> c
// if a is active, and b is equal to 2, deactivate a and activate c

a ~> b == 2 -> c
// if a is active, and b is equal to 2, activate c

a *-@ b = 2 -> c-b > 0 -> d
// if a is active, set b to 2, then if c minus b is greeater than 0, deactivate a, and activate d

a *-* b
// The trigger a raises the trigger b

a *-> b -> c > 0 -* d -> e
// If the trigger a is active, and the state b is active, and c is greater than 0, raise the trigger d, then deactivate b and activate e

```

### Fork Operators

Fork operators, `|-*` `|~*` `|->` `|~>` `|-@` `|~@` are used to indicate [Fork States](./States.md#Fork States), and they respect operation depth.

For example:

```

A |-> b == 0 -> First
  |-> b == 2 |-> e == "Yes" ~> Success
             |-> e == "No" -> Fail
             |~* Decided
  |~> b == 1 -* Number 1
  
```

This can be interpreted
> If A is active, and b is equal to 0 deactivate a and activate "First".  

> If A is active, b is equal to 2, and e is equal to "Yes", Activate Success without deactivating A, else if b is equal to 2, and e is equal to "No", activate "Fail" and deactivate A.

> If A is active and b is equal to 2, the "Decided" trigger will be raised without deactivating A. 

>If b is equal to 1, raise the trigger "Number 1", and deactivate A.


## Whitespace

Whitespace is used to indicate operation depth 

//TODO I'll do more on this later

## Flags

Flags are provided using curly braces `{}` and follow these rules:

* A number flag before any operation is used to indicate operation depth
* flags that are presented after an operation are used to modify that operation
* Any operation can have at most one flag clause, but that flag clause cna contain multiple comma-separated flags
* Flags that use areguments are specified using the colon `:` operator
    * Lists of arguments to flags are bounded by square-brace `[]` operators