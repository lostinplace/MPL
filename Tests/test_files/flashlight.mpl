flashlight: machine
    power: state
        on
        off

    battery: machine
        presence: state
            in
            out
        working
        charge: state
            empty
            low
            ok
            empty -> *
        level
        level > 1 ~> charge.ok
        1 > level ~> level > 0 ~> charge.low
        level <= 0 ~> charge.empty
        <Beam> -> level = level - 0.1

    power.on & battery.presence.in & battery.working & charge ~> <Beam>


