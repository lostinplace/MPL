# Concepts

## Engines

An Engine is a logical collection of state machines that all are evaluated in parallel.  One can imagine that a Person is an engine with state machines that represent the status of their circulatory system, respiratory system, nervous system, digestive system, and integumentary system.  When an Engine, "Steps" all of the associated machines step once, meaning all of their rules are evaluated in parallel once and only once.

## Context

The Context is a set of key-value pairs that is provided to the engine with every step.  There are two levels of Context available, the Engine-Level Context, that is available to all machines that operate within the Engine.

Take this set of key value pairs for example:

```
Context A

name: {Warn} "Foo"
handle: {Allow} "Foo"
Street: {Reject} "Bar"
City: {Resolve} "Bat"
State: {Resident: Allow, Employer: Resolve} "Baz"
UID: {Employer: Deny} "Baq"
```

When any machine's policy is evaluated, the above keys will be available to the machine's rules for evaluation.  Three types of key flags are identified above and are intended to resolve Assignment Conflicts.

Since all rules for machines are evaluated in parallel it is inevitable that rules will cause conflicts to occur when providing assigment instructions to the interpreter.  This is resolved using the keyflags system, given the concepts of Priority and Weight which are described in detail in later sections.

Given a set of competing assignments the question becomes, "how do we select an assignment, and what should we do with the assignments that aren't selected?"  The answers to this question differ by keyflag, but are provided in the [Assignments And Keyflags](Assignments and Keyflags.md) section of the docs. 


## Machines

Machines are collections of rules that describe the behaviors of an entity within the simulation.  They are described by a line with the following format

`Name : MACHINE`

A Machine is associated with a collection of States, Triggers, and a Context that is maintained by the MPL Engine but accessible outside of the machine.

A Machine is ultimately comprised of a collection of Definitions and Rules.

## Definitions

Within a machine, definition statements identify special symbols that can be used for the purpose of disambiguating identifiers.

The anatomy of a definition is:

```
Identifier : TYPE(Flags)
```

The following types are available:

```
MACHINE
STATE
TRIGGER
INT
DOUBLE
STRING
SET
DICT
BOOL
MACHINE
FUNC
```

More details are available in the [Types](./Types.md) section.

The MACHINE and STATE definitions allow child policies using leading white space.  This is best explained with an example:

```mpl
Car: MACHINE
  Running: STATE
  Driving: STATE(BLOCKING)
  Empty: STATE
  Radio: STATE
    On: STATE(EXCLUSIVE)
    Off: STATE(EXCLUSIVE)
  Fuel: CONTEXT(DOUBLE)
  Ignition: TRIGGER
```

The above policy describes a `MACHINE` Car, with several internal components:
* `Running` is a `STATE`
* `Driving` is a `STATE`
* `Empty` is a `STATE`
* `Radio` is a `STATE` with two child states
  * `On`
  * `Off`
* `Fuel` is a key from the `CONTEXT` with the type `DOUBLE`
* `Ignition` is a `TRIGGER`
  
Note that the `Working` state is flagged `BLOCKING`. This means that while the state is active, any attempt to activate the `Working` state while it is already active will fail. 

Also note that the `On` and `Off` states are flagged `EXCLUSIVE` which means that only one of them can be active at a time.  If the state `Car.Radio/On` is active, and the State `Car.Radio/Off` is activated, it will result in the deactivation of `Car.Radio/On`.

### Exclusive Shorthand

In the above example, we described a Car with a `Radio` that had two exclusive internal states, `On` and `Off`.  Since this behavior is relatively common in state machines, a shorthand is available:

```mpl
Car: MACHINE
  On: Radio
  Off: Radio
```

This will produce the same effect as the expanded definition that is provided above.

### Implicit Definitions

Since exhaustively defining the states of a system can be tedious and exhausting, symbols can also be defined implicitly, meaning that if a symbol is referred to, it's type will be inferred based on a set of rules.  These Rules are described in [Implicit Definition Rules](./Implicit%20Definition%20Rules.md).

The above definition of `Car` can be reproduced with the following shorthand and implicit definitions:

```mpl
Car: MACHINE
  Ignition *-> Running
  Driving: STATE(BLOCKING)
  On: Radio
  Off: Radio
  Fuel == 0.0 -> Empty
```

More information on how this policy can be evaluated is described below in the [Rules](#Rules) section.

## States

States are persistent attributes of a Policy that are tracked both internally and externally.  From a high-level, we can say that a state is what a Machine is currently "doing".  For example:

```
Cat in a Sealed Box: MACHINE
  Alive: STATE
  Dead: STATE
  
  Happy: Emotion
  Bored: Emotion 
```

The above policy describes a state machine for a theoretical cat in a sealed box.  This cat can be, "Alive", "Dead", or both "Alive and Dead at the same time".  The above policy also describes two emotional states that are exculsive substates of "Emotion".  This means that if the cat has an "Emotion" it can either be "Happy" or "Bored", but it cannot be both at the same time.

## Triggers

Triggers are a special class of state that are used for communication between machines and host processes.  When raised, a Trigger will remain active for only one step of the engine.  This means if it is not responded to immediately, the trigger will be ignored until it is raised again. 

Importantly, triggers may optionally specify a `VALUE` when they are raised, and this value will be available to the rest of the rule for the duration of its execution by using the `VALUE` keyword.

### Special Triggers

#### EVERY
The `EVERY` trigger accepts a time unit as an argument, and will present its self on every step after that interval has passed.  Please not that if this interval has been greatly exceeded, the trigger won't occur multiple times

For Example:

```mpl
Another One Bites The Dust: MACHINE
  EVERY(500ms) *-@ print("Another One Gone") -> Sang It
```

## Rules

Every state machine's policy is composed of definitions or Rules.  Definitions identify symbols that will be used within the Machine's policy, while rules describe the transitions that occur between states.

The general anatomy of a rule is as follows:
A. A trigger expression 
B. An origin state expression
C. A collection of actions, conditions, and branches
D. A target state expression

Each of these are optional, but a rule will always have at least:
* An Optional A
* Followed by an Optional B
* Followed by at least 1 from C or D

Consider the following example rule:

```Foo *-> Bar -> Bat```

This rule indicates that on a step, the Trigger `Foo` will cause a transition from the state `Bar` to the state `Bat`

## Transitions

A Transition describes the activation or inactivation of states within a rule.  This is easiest to describe with examples.

```
Foo -> Bar
```

> Given a Machine with States `Foo` and `Bar`.  On a Step, If the state `Foo` is active, activate `Bar`, and deactivate `Foo`

This pattern of activation of a target and deactivating the origin is called a "consuming" transition.  This means that the origin state is "consumed" to produce the target state.  This kind of transition is indicated with the "-" character in the transition indicator for the rule

Contrast this with the following

```
Foo ~> Bar
```

This says that as long as the state `Foo` is activated, the state `Bar` should be activated.  This transition does not consume the `Foo` state, meaning it will remain active after the transition occurs

## Relational Pathing

Since the context of a Machine can include references to other machines as well as nested data structures, the following relative pathing rules are available:

### Triggers
Triggers are accessible using the `.` Operator. Note that triggers can be observed from anywhere, but can only be raised by the Machine that defined them.

For Example:

```mpl
Box: MACHINE
  Shaken *-* Shaking
  
Heater: MACHINE
  My Box : MACHINE {SRC:Box}
  
  My Box.Shook *-@ print("I'm being shaken")
```

### States
States are observable to any other machine, but again, they cannot be activated or deactivated through consumption of a state unless the CONSUMES flag allows this behavior.  They are accessible using the 

For Example:

```mpl
Box: MACHINE
  Contents: MACHINE {SRC: Stuff, CONSUMES:[Extreme Temp/ALL], PRODUCES:[On, Off]}
  Too Hot: Extreme Temp
  Too Cold: Extreme Temp
  
  EVERY(10s) *-@ temp = ReadSensor() {NO-CACHE} |-> temp < 20 -> Need Heat
                                                |-> temp > 40 -> Need Cooling
                                                |-> 20 <= temp <= 40 -> !Extreme Temp
  
  Contents/On ~> Contents Active
  Contents/Off ~> !Contents Active
  
Heater: MACHINE
  My Box : MACHINE {SRC:Box, PRODUCES:[Extreme Temp/ALL]}
  ENTER -> Off
  On: Power
  Off: Power
  
  On ~@ AddHeatWatts(1)
  My Box/Extreme Temp/Need Cooling -> Off
  My Box/Extreme Temp/Need Heat -> On
```

## Steps

When a machine, "Steps" all of its rules are evaluated once.  

The easiest way to conceptualize this is with an example:

```mpl
Car: MACHINE
  ENTER -> Off
    
  Running: Motor
  Stopped: Motor
  
  Key Inserted *-> Key Present
  Key Removed *-> !Key Present
  
  Key Present & Ignition:TRIGGER *~> Off -> Starting
  
  Starting -> Fuel >= 0 -> Running
  
  Adding Fuel *-@ Fuel += VALUE {1} 
  Running | Starting ~@ Fuel -= 1
  
  !Key Present ~> Stopped
  Fuel <= 0 ~> Stopped
  
  Stopped -> Off
```

The above policy describes a machine `Car` that operates in a recognizable way.  It has a default `Off` state that is set when the machine is initialized.  It has a motor that can be either Running or Stopped.  It has an `Ignition Trigger` that can be raised once the key is present, which is controlled by triggers that can be provided by the host process.

In describing steps, we should take care to note what happens when.

On a single step of the Engine hosting this Machine, a few things will be true.

* If a key is not present, you cannot insert a key and trigger the ignition and expect the car to be `Starting`
* A Car will never be starting and running at the same time.
* If a car is starting while the `Fuel` is 0 and the `Adding Fuel` Trigger is raised, it will not start.

In order to process these events, the Engine must step a 2nd time.  This leads us to the need for **Step Modes**

### Step Modes

#### Step Once

The default engine step mode is **Step Once**, which means all rules of the associated machines will be evaluated once, the state after 1 step will be returned, and the triggers raised by that step will be raised to the host process in order of ocurrence (from left to right rule depth).

#### Step N

The **Step N** Mode indicates that the engine should step `N` times before returning the new context and raising triggers in order of presentation.

#### Step Until Timeout

The **Step Until Timeout** mode indicates that the engine should step until either its allocated time has passed.  This behavior can be adjusted by passing the `SuspendWhenStable` flag, which will suspend and return the context and triggers once the Engine has reached a Stable state (no changes to the context or state of the engine have occurred in the past 2 steps).

At any time, the engine can be forced to return the result of the lat completed Step by calling the `SuspendAndReturnLatest` method on the engine.

---