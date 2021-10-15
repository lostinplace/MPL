Wumpus: MACHINE

    Ok: Health
    Hurt: Health
    Dead: Health

    Hurt ~@ Turns Wounded: INT += 1
    Ok ~> Turns Wounded > 0 ~@ Turns Wounded -= 1

    Stab *~> Ok -> Hurt
    Stab *~> Hurt -> Dead

    Recover:Activity ~> Hurt -> Ok

    Wander: Activity
    Hunt: Activity
    Attack: Activity
    Flee: Activity
    Recover: Activity

    Mindset: STATE
        Smell Prey: STATE
        Feel Secure: STATE
        Near Prey: State

        Enter Smell Zone *~> Smell Prey
        Exit Smell Zone *~> Smell Prey -> 0

        0 & Ok: Health ~> Feel Secure
        Hurt: Health ~> Feel Secure |-> {Turns Wounded} -> 0
                                    |-> {10} -> Feel Secure

        Enter Strike Zone *~> Near Prey
        Exit Strike Zone *~> Near Prey -> 0

    Smell Prey & Feel Secure ~> Wander -> Hunt
    Smell Prey & !Feel Secure ~> Wander -> Flee

    Near Prey & Feel Secure ~> Hunt -> Attack
    Near Prey & !Feel Secure ~> Attack -> Flee

    !Feel Secure & !Smell Prey & Hurt ~> Flee -> Recover





