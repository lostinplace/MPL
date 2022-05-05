# Abstract

In the development of any complex software, the vast majority of a programmer’s time and effort will go to state management.  This is in part because nearly all modern programming languages are designed to offer sequences of instructions that allow the programmer to manage the state of the computer, without offering any high-level description of the transformations that the computer will undergo over the course of a program’s execution.  MPL, short for “Machine Policy Language” is a system for describing complex hierarchical state machines using a language that roughly approximates the human-language (both visual and auditory) description of conceptual state machines.  An MPL Policy consists of States, Machines, and Rules.  States are references that can be either active or inactive, and are comprised of optional exclusive child states.  Machines are collections of States, Machines and Rules that can be either active or inactive, but their activity need not be exclusive.  Rules are descriptions of the transitions in activation between States and Machines.  Using these simple formalisms (inspired by [StateCharts]([Harel’s StateCharts]([https://www.sciencedirect.com/science/article/pii/0167642387900359](https://www.sciencedirect.com/science/article/pii/0167642387900359))) many state management tasks that would in a typical programming language require a great deal of code, become trivial to author and observe.


# Introduction

Computer Programmers, AKA Software Developers, Software Engineers, are at their best people that convert expectations about the state of a system into sequences of instructions to be executed by a computer with the goal of producing those expected states at the expected times.

There’s a lot of reasons for that, including the story of [Alan Turing’s Thesis Advisor]([https://en.wikipedia.org/wiki/Alonzo_Church](https://en.wikipedia.org/wiki/Alonzo_Church)) and the way semiconductors can be manufactured at scale, but it’s important to note that the fact that we employ people to translate ideas from one form into another is kind of weird, since most of the systems we build are in fact processes that convert one kind of data into another.

For example, at this point, you’ve just read two plain-english-language paragraphs, and you (hopefully) understand what they said, and you could (probably) relay the ideas in those paragraphs to friends in a way they could understand and relay them to others and so on.  All of that could happen without anyone issuing a single instruction.  This is weird, but if you read those first two paragraphs again, you’ll note that there are precisely 0 explicit instructions, but as a set of data that implicitly comprises an explanatory system, it produced understanding.

This is an observation that has been bugging me for years. The typical use of human language is almost exclusively about describing states, and transitions between those states, but we don’t have any computational languages focused on these formalisms.

If you’ve found yourself down this rabbit hole before, you might at this point say, “What about [Harel’s StateCharts]([https://www.sciencedirect.com/science/article/pii/0167642387900359](https://www.sciencedirect.com/science/article/pii/0167642387900359)) or [PlantUML State Diagrams]([https://plantuml.com/state-diagram](https://plantuml.com/state-diagram))” but what I would present to you is the question, can you describe a simple computational program using only those tools?  You know what, I’ll even give you a break on part of it. Can you use those tools to provide a set of diagrams that create the same level of understanding of a todo list app that you got from the ideas from my first two paragraphs?

If you can, please let me know how. I would love to adopt your tools, but until then, I think we need some new ones.

To that effect, I offer MPL, or “Machine Policy Language”:  A system for easily describing state machines that are useful to people who are asked to produce software.


# Data Structures

At its core, MPL is a set of assertions about some data structures and relationships between those structures.  The core primitive structures in MPL are listed below, along with a brief outline of their composition.



* States
    * The core structure of MPL, which has an associated unordered set
    * Is considered Active when its associated set has non-zero values
    * May Include many States as children
    * Only one of a state’s children may be active at any given time
* Rules
    * Act as a description of the transitions that exist between States
    * Are applicable only when every clause’s conditions are met
    * All rules are evaluated in parallel
    * Composed of clauses separated by Operators
    * Operators
        * Observe Operator
            * Passes the unordered set {True} to the RHS when the LHS is active
        * Consume Operator
            * Transfers the value of the LHS to the RHS
    * Clauses
        * Query Clauses
            * Algebraic Query
                * Allows for simple algebraic operations
            * State Query
                * Allows the user to target multiple entities for observation/consumption 
        * Action Clauses
            * Target Clauses
                * Assign the results of query clauses to targeted States
            * Assignment Clauses
                * Assigns the value RHS to the indicated state LHS
        * Scenario Clauses
            * Describes the mechanisms for conflict resolution
* Machines
    * Can include many States as Children
    * Can include many Machines as Children
    * Any number of a Machine’s children may be active at the same time
    * Can include Rules
* Triggers
    * Special kinds of states without children that are Active only as long as the conditions that activate them are met


# Basic Docs (WIP)

MPL differs from most computational languages in that the core primitive is not “the instruction”.  MPL has at its core two primitives, **States** and **Rules.**


## States

States are named entities with associated unordered sets of values (integers, strings, references).  A state is considered **Active** when its associated set of values is not empty, and **Inactive** when it has values.

The easiest example of a state to keep in mind is the **_Power_** state.  Power can either be on or off, it can’t be both on or off at the same time, so when the **_Power_** state is active, we know that at a minimum it’s associated set is _{True}_.


## Rules

Rules are a description of a sequence of queries and actions separated by operators that describe the transistion between those clauses.  A Rule is considered **Applicable** when all oof the queries described produce **Active** values, and when all of the actions described are valid.


### Rule Operators

Before we define queries and actions, let’s talk about the two main Rule Operators in MPL, these are the **Observe** operator, and the **Consume **operator


#### Observe

The **Observe** operator, denoted `**~>`**  (tilde-arrow) yields a _{True} _result when the query to the left is **Active**. For Example

```mpl

Tired ~> Cranky

```

This means that when the state **Tired** is observed to be **Active**, the state** Cranky** should be **Active**.  This is described in two clauses, a query clause that is simply `**Tired` ** and special type of action clause called a **Target Clause** (because it is the rightmost clause in the rule) which targets the state **Cranky**.

It should be noted that if the value to the left of the observe operator is not **Active** the rule is considered to be not applicable.


#### Consume

The **Consume** operator, denoted **`->**` (skinny arrow) yields the value of the query to its left, and clears the value of directly referenced states, “consuming” them, and transferring their value to the rule’s value cache.  These values will eventually be assigned to the state targeted by the rule’s **Target Clause**, but for now they are held in limbo for the purpose of this rule’s interpretation.

For Example:

```mpl

On -> Off

```

This example can be read, “Off consumes On” meaning that when the state On is **Active**, its value is consumed, and is assigned to the state Off.  When this rule is resolved, Off will be **Active** and On will be **Inactive**.


### Queries


#### State Queries

State Queries are a type of clause that yield a set of values to the Rule operator on their right, and exposes the states to consumption or targeting.  In the above examples you’ve seen some simple, single-state queries, but more complex queries are available.  For example:

```mpl

On & High Volume ~> Loud

Good | Bad -> It will be alright

Right ^ Left -> Direction Chosen

```


#### Algebraic Queries

Algebraic Queries are a type of clause that yield a set of values to the Rule operator on their right after pperformmin some kind oof transformation on the values presented.  Algebraic queries can be consumed or observed, but consuming them does not affect the States that they collected values from.

For Example:

```mpl

Level &lt; 1 -> Low

Message == `safe` -> Safe

Principal * 0.1 -> Interest

```

In all of the above cases, the values produced by the algebraic queries are passed on to the target clause on the right, but noe of those states will be changed.

It should be noted that in order for a rule to be **Applicable**, all Algebraic Query Clauses must yield values that are **Active** meaning that hey produce values that are not False, or 0-equivalent.


### Actions


#### Target Clauses

The rightmost-clause in any rule is known as a Target Clause, meaning that references targeted by queries in this clause will be assigned values from previous parts of the Rule.  References in algebraic queries will not be targeted, and the rules for state queries are a little different.  

For example:

```mpl

A -> B & C

# The value of A is consumed, and assigned to both B and C, regardless of whether they are true

A -> B | C

# B or C are chosen with equal probability, the value of A is assigned to the chosen reference

A -> B ^ C

# If only one of B or C are Active, then it targets the active one.  If none are Active, it targets B.  If both are active, the rule is not applicable

```


#### Assignment Clauses

An assignment clause allows direct assignment of a value to a reference.  Consuming an assignment clause produces the value of the expression’s right-hand-side value.

For Example:

```mpl

Tank Full ~> Number of Gallons = Tank Volume * 0.99

```
