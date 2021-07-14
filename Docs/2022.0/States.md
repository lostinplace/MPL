## Conditional States

Conditional states are a special class of state that are synthesized from [logical expressions](./Expressions.md).  Consider the following:

```
money > 0 -* Has Money -> Not Broke 
```

This rule evaluated the key `money` from the context, and if it is greater than 0, the trigger, `Has Money` is raised then the state, `Not Broke` is activated.  Importantly, the hard dash "-" as opposed to the soft dash "~" indicates that the state will be "consumed" when the step occurs.  This means that on the next step, this rule will not be evaluated unless the value of `money` has changed, which means that the trigger `Has Money` will only be raised once every time the value of `money` changes and is greater than 0.

Contrast this with the following

```
money > 0 ~* Has Money -> Not Broke 
```

In this case, the soft dash "~" indicates that the state is not consumed, which means that the trigger `Has Money` will be raised on every step of the machine where the value of `money` is greater than 0.

Note that in order for a rulee to be executed, all conditional states within the rule must evaluate to True.

## Holding States

Holding states are a way to capture a previous evaluation and "remember" that a rule can continue progress without completely restarting on the next step.

Consider the following example:

```
Button *-> Door Closed -* Pressed Button(VALUE.time) -> Puzzle Solved & Lever Pulled -* Door Opened(VALUE.player) -> Door Open & Lever Reset
```

this can be interpreted:
> In order to open the door, it must be closed, you must solve the puzzle, and pull the lever.  Then the pressed button trigger will be raised with the time, the door opened trigger will be raised with the player that pressed the button, the door will be open and the lever will be reset

This works alright, but it means that you must press the button first, or create a separate state to track whether the button has been pressed.  If we want to record the pressing of the button implicitly, we can specify a **Holding State** using the `->>` operator seen here:

```
Button *-> Door Closed -* Pressed Button(VALUE.time) ->> Puzzle Solved & Lever Pulled -* Door Opened(VALUE.player) -> Door Open & Lever Reset
```

With this change, the system will record the time that the button was pressed (but won't raise the trigger yet)  Once the puzzle is solved and the lever are pulled, the door will be opened without having to press the button again.


## Action States

Action states are a special class of state that produces side effects.  They are exclusively comprised of [assignment expressions](Expressions.md#Assignment_Expressions) or [function expressions](Expressions.md#Function_Expressions) and are indicated using the left-hand `-@` operator.

In order for the action described by an action state to be taken, it must be accepted according to its **Priority and Weight**(see [Assignments and Keyflags](Assignments%20and%20Keyflags.md)).  If the change is **Rejected** subsequent actions and transitions will not be executed.

Consider the following example:

```

Ball Passed *-> In Scoring Position -> Shoot(VALUE) -@ score += 1 -> Scored A Point

```

This rule can be interpreted as follows:
> If a ball is passed, and the machine is in scoring position,  a shot is attempted.  If the shot is successful the score is incremented by 1

Contrast this with the following example of two competing rules:
```
Ball Passed *-> In Scoring Position ~> Shoot(VALUE) -@ score += 1 -> Scored A Point

Ball Passed *-> Lucky -@ score +=2 -> Got a lucky shot

```

In this case, a machine in scoring position may score a point, but a "Lucky" machine will score two points.  In the event that `Shoot` returns True and the Machine's `Lucky` state is active, there will be two competing edits to the score.

Since no priorities or weights are specified, there is a 0.5 probability that the score will be incremented by 1 instead of 2. Since the default keyflag for these edits is `Allow`, both rules will complete their execution, and the final state in these events will reflect the activation of `Scored A Point`, and, `Got a Lucky Shot` and the inactivation of `Lucky`

Contrast this with the following:

```
score: CONTEXT{Reject}

Ball Passed *-> In Scoring Position ~> Shoot(VALUE) -@ score += 1 -> Scored A Point

Ball Passed *-> Lucky -@ score +=2 -> Got a lucky shot

```

In this case, whichever rule gets selected will be the only one that impacts the final state.  this means that If the Machine is `Lucky` and its `Shoot` is successful:

* there is a 0.5 probability that the machine will have incremented the score by 1, and `Scored a Point`, it's Lucky state will remain active, and `Got a lucky shot` will remain inactive
* there is a 0.5 probability that the machine will have incremented the score by 2, and `Got a lucky shot`, it will no longer be `Lucky` and it will not have `Scored A Point`.


## Fork States

Sometimes there are repetitive states that have the same general criteria for starting, but differ in their eeveentual destination based on logic or selection.  To simplify this, we can use **Fork States**

Consider the following example:

```
At Stop Sign -> Road Is Clear -> Going Left -* Turning Left -> Turned Left
At Stop Sign -> Road Is Clear -> Going Right -* Turning Right -> Turned Right
At Stop Sign -> Road Is Clear -> Going Straight -* Driving Forward -> Went Straight
```

This Repetition is tedious and we can make it simpler using fork states as shown using the `|->` operator:

```
At Stop Sign -> Road Is Clear |-> Going Left -* Turning Left -> Turned Left
                              |-> Going Right -* Turning Right -> Turned Right
                              |-> Going Straight -* Driving Forward -> Went Straight
```

Alternately, fork states will accept [Priority and Weight](./Assignments%20and%20Keyflags.md) arguments as shown below:

```
At Stop Sign -> Road Is Clear |-> {left priority, 0.3} -* Turning Left -> Turned Left
                              |-> {right priority, 0.3} -* Turning Right -> Turned Right
                              |-> {0.4} -* Driving Forward -> Went Straight
```

using this syntax, the driver can express a priority level for either left or right turns, and the highest priority will determine the selection.  If the left and right priorities are zero or undefined, a random selection will be made with a aggregate 0.6 for left or right, or 0.4 for straight.  

## Timed States

Timed states are a way of communicating the passage of time in state transitions.  These are communicated using descending order time unit notation, and are evaluated as conditional expressions that will only evaluate to true once the specified unit of time has passed.

The available time units are

| Abbreviation | Unit     |
| :------------- | :----------: |
|p| Steps |
|d| Days   |
|h| Hours  |
|m| Minutes|
|s| Seconds|
|ms| Milliseconds|

For example:

| Rule | When Does it Execute     |
| :------------- | :----------: |
| `Begin *-> Origin -> 5p -> Destination`| Destination is activated 5 steps of the engine seconds after `Begin & Origin` occurs|
| `Begin *-> Origin -> 30s -> Destination`| Destination is activated 30 seconds after `Begin & Origin` occurs|
| `Begin *-> Origin -> 2d4h30m -> Destination`| Destination is activated 2 days, 4 hours and 30 minutes after `Begin & Origin`|
| `Begin *-> Origin -> 0.0001ms -> Destination`| Destination is activated the next step after `Begin & Origin`|

## Adjustment States

Since the host process will receive `Trigger` events in the order they are raised by rules, sometimes we will want to delay their presentation to the host process.

Consider the following example:

```
Treat Bin Opened *-> Dog Sleeping -* Dog Hungry -> Dog Awake
Treat Bin Empty -> No Backup -@ Order Treats -* Process Order -*Receive Estimate -> Awaiting Order
```

In this event, if the `Treat Bin Opened` trigger is raised on the same Step that the `Treat Bin Empty` and `No Backup` states are active, the host process will receive Trigger callbacks in the following order:

```
Dog Hungry
Process Order
Receive Estimate
```

This is because the priority of Trigger raises is the distance from the leftmost operation in the rule that raised them.  In this case, the priority of `Dog Hungry` is 2, `Process Order` is 3 and `Receive Estimate` is 4 

Since we may want to have an estimate before dealing with a hungry dog, we can use **Adjustment States** to adjust the presentation order 

### ADJUST(n)

The `ADJUST(n)` state allows us to adjust the delay of any subsequent triggers by a known number of left->right steps.  

for example:

```
Treat Bin Opened *-> Dog Sleeping -> ADJUST(4) -* Dog Hungry -> Dog Awake
Treat Bin Empty -> No Backup -@ Order Treats -* Process Order -*Receive Estimate -> Awaiting Order
```

This would result in a new priority for `Dog Hungry` of 6 

### ADJUST(State Expression)

The `ADJUST(State Expression)` state allows us to adjust the delay of any subsequent triggers until other triggers are raised (as long as those triggers are raised at all)

for example:

```
Treat Bin Opened *-> Dog Sleeping -> ADJUST(Process Order & Receive Estimate) -* Dog Hungry -> Dog Awake
Treat Bin Empty -> No Backup -@ Order Treats -* Process Order -*Receive Estimate -> Awaiting Order
```

This would result in `Dog Hungry` being Raised immediately after `Process Order` and `Receive Estimate`.  If neither of those triggers are queued to be raised to the host process, then `Dog Sleeeping` reverts to its original priority of 2.  