Wumpus: MACHINE
    Health: STATE
        Ok
        Hurt
        Dead

    0 ~> Health/Ok

    Hurt ~@ Turns Wounded: INT += 1
    Ok ~> Turns Wounded > 0 ~@ Turns Wounded -= 1

    Stab *~> Ok -> Hurt
    Stab *~> Hurt -> Dead

    Activity: STATE
        Wander
        Hunt
        Attack
        Flee
        Recover

    Activity/Recover ~> Hurt -> Ok

    0 ~> Activity/Wander

    Mindset: MACHINE
        Smell Prey: STATE
        Near Prey: STATE
        Feel Secure: STATE

        Distance To Prey < Smell Range -> Smell Prey
        Distance To Prey > Smell Range -> Smell Prey -> 0

        0 & Ok: Health ~> Feel Secure

        Hurt: Health ~> Feel Secure -% Turns Wounded -> 0
        Hurt: Health ~> Feel Secure -% 10 -> Feel Secure

        Enter Strike Zone *~> Near Prey
        Exit Strike Zone *~> Near Prey -> 0

    Smell Prey & Feel Secure ~> Wander -> Hunt
    Smell Prey & !Feel Secure ~> Wander -> Flee

    Near Prey & Feel Secure ~> Hunt -> Attack
    Near Prey & !Feel Secure ~> Attack -> Flee

    !Feel Secure & !Smell Prey & Hurt ~> Flee -> Recover
