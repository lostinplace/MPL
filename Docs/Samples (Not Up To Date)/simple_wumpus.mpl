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
        Near Prey: STATE
        Feel Secure: STATE

        Enter Smell Zone *~> Smell Prey
        Exit Smell Zone *~> Smell Prey -> VOID

        0 & Ok: Health ~> Feel Secure
        Hurt: Health ~> Feel Secure |-% Turns Wounded -> VOID
                                    |-% 10 -> Feel Secure

        Enter Strike Zone *~> Near Prey
        Exit Strike Zone *~> Near Prey -> NOT Near Prey

    Smell Prey & Feel Secure ~> Wander -> Hunt
    Smell Prey & !Feel Secure ~> Wander -> Flee

    Near Prey & Feel Secure ~> Hunt -> Attack
    Near Prey & !Feel Secure ~> Attack -> Flee

    !Feel Secure & !Smell Prey & Hurt ~> Flee -> Recover
