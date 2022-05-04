flashlight: machine
    battery: machine
        charge: state
            empty: state
            low: state
            ok: state
        inserted: state
            no: state
            yes: state
            no -> *
        level: state
        !inserted ~> level.* & charge.*
        <Beam> ~> level = level-0.1
        inserted & level < 1 ~> level > 0 ~> charge.low
        inserted & level > 1 ~> charge.ok
        inserted -> inserted.yes
        inserted ~> level <= 0 ~> charge.empty
    broken: state
    power: state
        off: state
        on: state
    power.on & battery.inserted & !broken & !battery.charge.empty ~> <Beam>

---
Beam: {True}
flashlight.battery.charge.ok: {True}
flashlight.battery.inserted.yes: {True}
flashlight.battery.level: {1.40000000000000}
flashlight.power.on: {True}
