# Engine Context

## Overview

This is how reference values are stored in the engine.

## API

behaviors:

### Adding

Adding a reference expression with a set of types does the following:

Establishes a novel value in the dictionary mapped to a Reference with an empty type set

creates an "is a" relationship between the empty-typed Reference and the types

### Lookup

Lookup by emmpty-typed reference will always retrurn the referrence by name

types in the reference lookups are ignoreed except in the eveent of teemplated names, where only typees will be respected 