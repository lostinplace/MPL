# Reference Resolution

This details the rules for references in mpl.

in general, all names aree unique within their local context.  This means that you can not have the following:

```mpl
One: machine
One: state
```

## Inheritance

using the colon operator signifiees that the defined reference inherrits the rules of the referred parent.  For instance:

```mpl
robot: machine
    A->B
    
Astro: robot
    *->B
    B->C

Data: robot
    *->C
    C->D
    One->Two
```

This can be interpreted as follows:

***robot*** is a machine with one rule:
1. `A->B`

it has two states, A and B.

they can be rewritten from the perspective of the engine as:
"robot.A" and "robot.B"

***Astro*** is a robot with three rules:
1. `*->B`
2. `B->C`
3. `A->B` (Inherited from robot)

It has three states, A, B and C.
the states can be rewritten from the perspective of the engine as:
"Astro.A" and "Astro.B" and "Astro.C"

***Data*** is a robot with four rules:
1. `*->C`
2. `C->D`
3. `One->Two`
4. `A->B` (Inherited from robot)

It has six states, A, B, C, D, One and Two.

They can be rewritten from the engine context as, "Data.A", "Data.B", "Data.C", "Data.D", "Data.One" and "Data.Two".

## Child Access

The children of any machine, including the engine can be accessed using the dot operator.  For instance:

```mpl
robot: machine
    A->B
    Arm: machine
        *->B
        One->Two
    Reactor: machine
        power: state
            On
            Off
    *-> Reactor.power.Off
    <switch> -> Reactor.power.On -> Reactor.power.Off
    <switch> -> Reactor.power.Off -> Reactor.power.On
```


    




