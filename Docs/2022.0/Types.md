# Types

This is the list of types that is supported by MPL

````
MACHINE
  Flags: SRC:[Path/Name], CONSUMES:[STATES], PRODUCES:[STATES], Warn, Allow, Reject, Resolve, Deny
STATE
  Flags: Exclusive, Blocking
TRIGGER
  Flags: INT, DOUBLE, STRING, DICT[TYPE,TYPE], BOOL 
LIST:
  Flags: TYPES:[TYPE], Warn, Allow, Reject, Resolve, Deny
INT
  Flags: Warn, Allow, Reject, Resolve, Deny
DOUBLE
  Flags: Warn, Allow, Reject, Resolve, Deny
STRING
  Flags: Warn, Allow, Reject, Resolve, Deny
DICT[TYPE,TYPE]
  Flags: Warn, Allow, Reject, Resolve, Deny
BOOL
  Flags: Warn, Allow, Reject, Resolve, Deny  
FUNC
  Flags: {PARAMS:[Types], RETURN: Type, CACHE, NO-CACHE, Warn, Allow, Reject, Resolve, Deny} 
```