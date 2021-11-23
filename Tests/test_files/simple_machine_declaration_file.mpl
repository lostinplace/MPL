base: machine
    base state 1: state
    base state 2: state
    complex state: state
        complex state layer 1a:state
            complex state layer 2a
            complex state layer 2b
            complex state layer 2c
        complex state layer 1b:state
    sub machine: machine
        sub machine state a:state
        sub machine state b:state

    base state 2 -> test variable > 10 ->  complex state layer 2a
