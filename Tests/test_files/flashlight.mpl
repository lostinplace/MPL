flashlight: machine
    power: state
        on
        off

    battery: machine
        inserted: state
            yes
            no -> *
        inserted -> inserted.yes
        !inserted ~> level.* & charge.*

        charge: state
            low
            ok
            empty

        inserted & level > 1 ~> charge.ok
        inserted & level < 1 ~> level > 0 ~> charge.low
        inserted ~> level <= 0 ~> charge.empty
        <Beam> ~> level = level - 0.1

    broken: state

    power.on & battery.inserted & !broken & !battery.charge.empty ~> <Beam>



