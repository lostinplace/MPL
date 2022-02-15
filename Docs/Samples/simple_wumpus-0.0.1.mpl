Wumpus: machine
    Health: state
        Ok
        Hurt
        Dead

    * ~> Ok

    Hurt ~@ Turns Wounded += 1
    Ok ~> Turns Wounded > 0 ~@ Turns Wounded -= 1

    <Stab> ~> Ok -> Hurt
    <Stab> ~> Hurt -> Dead

    Activity: state
        Wander
        Hunt
        Attack
        Flee
        Recover

    Recover ~> Hurt -> Ok

    * ~> Wander

    Mindset: machine
        Smell Prey: state
        Near Prey: state
        Feel Secure: state

        Distance To Prey < Smell Range -> Smell Prey
        Distance To Prey > Smell Range -> Smell Prey -> *

        * & Ok ~> Feel Secure

        Hurt ~> Feel Secure -> %{Turns Wounded} -> *
        Hurt ~> Feel Secure -> %{10} -> Feel Secure

        <Enter Strike Zone> ~> Near Prey
        <Exit Strike Zone> ~> Near Prey -> *

    Smell Prey & Feel Secure ~> Wander -> Hunt
    Smell Prey & !Feel Secure ~> Wander -> Flee

    Near Prey & Feel Secure ~> Hunt -> Attack
    Near Prey & !Feel Secure ~> Attack -> Flee

    !Feel Secure & !Smell Prey & Hurt ~> Flee -> Recover
