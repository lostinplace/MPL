# Reference Resolution Rules (Q3 2021)

1. All names must be unique by type
2. a reference usage of a different type spawns a separate reference of the used type.  This is insecure, because it means that refernces can be secretly multi-purposed.  Not only should this be ledgered, but refernces should be lockable
3. all triggers exist in a global space with a reference to the source of the trigger.
4. We're not currently


## Notes

dependency resolver establishes the in-memory representation of the machine

I start by traversing the tree to figure out what all the references are.  If they're defined in a declaration expression, they're assumed to be states.  the reference should be tracked as 

vars = Reference(name, None) -Described By-> Reference(name, type): MPL{type}

edges:  

`described by` is the fully_typed reference, at the end of resolution, every reference should be fully described

`instantiated as` is the actual value that represents the state of the reference.

`used in` traces the clauses that yielded the reference

`child of` associates clauses to rules.  Also traces states' parents

`assigned in` traces clauses that impact the reference.  This includes state activations

`consumed in` traces the consumption of states and machines activity to the rules that impact them





