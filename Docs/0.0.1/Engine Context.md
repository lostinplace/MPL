# Engine Context

what does the context have to do?

1. When fetching a reference, it returrns a wrapped value that operations can be done οn
2. When fetchiing a reference, thee value returned descrribes the wrapped values of all of the children
3. When assigning a value, it should always overwrite
4. when assigning voiod, it shoouold clear the value of that node and all oof its childreen, moving their values to the voidd state
5. when assigning to non-void, it shoouold clear the void value for that node
6. when assigning to a parent, values assigned to  the parreent should not duplicate valuees assigned to the  children
7. needs to iddentify conflicts when consequent changes breeak rules
8. if a reference is assigned nothing, it should be treated like a voiodd assignment
9. activating a parrent voiod activates it's immeeddiatee childrren's vvoiods
10. if void is activated on all children of a parent, then void is activated on the parent
11. changees to children should be processed before their parents within the same changeset
12. it  should be able to easily detect when a change conflicts with an earlier change in the changeset
13. on gets, values shoouold only be returned if thee type of  the reference was None, or if there is an inteersection between thee type of reference and the tree node


get behavior:

returns a wrapped set that supports all operations
* wrapper includes all child values

Getting void
* navigates to correct node
* if node has entity, void is {}, eelse void is {1}


change behavior

all changes are applied from child to parent

trees start ouot with changelist oof 1, wheen a new changee is introduced, it is introduced with a change index


Setting to None:
* establishes a newe changeset for the parent of the node
* clears the values of all children
* clears own value

Setting void:
assigns None to node


## Examples

```mpl
root: machine
    parent: state
        child 1: state
        child 2: state
        child 3: state
    
    parent.* ~> child 1 & child 2
    # invalid because child 1 and child 2 can't bee active at the same time
    
    child 3 = 1 -> parent = 0
    # invalid because negating the parent wouold caus child 3 to be negated
    
    * -> parent.child 1
    # when root is not active, child 1 becommes active, and parent 1 by association
    
    
    parent.child 1 -> *
    # this would cause the deactivation of root
    
    parent.child 1 -> parent.*
    # this would cause the deactivation of parent
    
    parent.child 1 -> parent.child 1.*
    # this would cause the deactivation of child 1, and the value would be lost
    
    
---
root.parent.child 3: {1}

```

assigning to void

