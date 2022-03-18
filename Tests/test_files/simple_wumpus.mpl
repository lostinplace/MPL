Wumpus: machine
    Health: state
        Ok
        Hurt
        Dead

    * ~> Health.Ok

    Health.Hurt & <Turn Ended> ~@ Turns Wounded += 1
    Health.Ok & <Turn Ended> ~> Turns Wounded > 0 ~@ Turns Wounded -= 1

    <Stab> ~> Health.Ok -> Health.Hurt
    <Stab> ~> Health.Hurt -> Health.Dead

    Activity: state
        Wander
        Hunt
        Attack
        Flee
        Recover

    Activity.Recover ~> Health.Hurt -> Health.Ok

    * ~> Activity.Wander

    Mindset: machine
        Smell Prey: state
        Near Prey: state
        Feel Secure: state

        Distance To Prey < Smell Range -> Smell Prey
        Distance To Prey > Smell Range -> Smell Prey -> *

        Smell Prey & Feel Secure ~> Wander -> Hunt
        Smell Prey & !Feel Secure ~> Wander -> Flee

        <Enter Strike Zone> ~> Mindset.Near Prey
        <Exit Strike Zone> ~> Mindset.Near Prey -> *

    Mindset.* & Health.Ok ~> Mindset.Feel Secure

    Health.Hurt ~> Mindset.Feel Secure -> %{Turns Wounded} -> *
    Health.Hurt ~> Mindset.Feel Secure -> %{10} -> Mindset.Feel Secure





    Near Prey & Feel Secure ~> Hunt -> Attack
    Near Prey & !Feel Secure ~> Attack -> Flee

    !Feel Secure & !Smell Prey & Health.Hurt ~> Flee -> Recover
