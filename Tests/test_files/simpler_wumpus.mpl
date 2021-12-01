Wumpus: machine
    Health: state
        Ok
        Dead

    * ~> Ok

    <Stab> ~> Ok -> Dead

    Activity: state
        Wander
        Attack
        Flee

    * ~> Wander

    Mindset: machine
        Smell Prey: state
        Feel Secure: state

        Distance To Prey < Smell Range -> Smell Prey
        Distance To Prey < Smell Range -> <Snarl>

        Distance To Prey > Smell Range -> Smell Prey -> *

        * & Ok ~> Feel Secure

    <Enter Strike Zone> ~> %{9} -> Feel Secure -> Attack
    <Enter Strike Zone> ~> Feel Secure -> Flee
    <Hunter Died> ~> Attack -> Wander

    !Smell Prey & Flee ~@ noise = `safe` ~> Feel Secure
    Feel Secure ~@ noise = `wandering` -> Wander
