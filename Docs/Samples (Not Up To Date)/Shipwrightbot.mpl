Robot: MACHINE
    Ship: STATE
        Receive Spec(spec: Specifications) *->  Awaiting Specifications -> Ship.spec = spec -> Specification Received
        Specification Received -> `IsReady(Ship.spec:Specifications)` /-> -> Designing


        Designed: STATE