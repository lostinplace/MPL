Wumpus: machine
    Activity: state
        Attack: state
        Flee: state
        Hunt: state
        Recover: state
        Wander: state
    Health: state
        Dead: state
        Hurt: state
        Ok: state
    Mindset: machine
        Feel Secure: state
        Near Prey: state
        Smell Prey: state
        <Enter Strike Zone> ~> Near Prey
        <Exit Strike Zone> ~> Near Prey -> 0
        Distance To Prey < Smell Range -> Smell Prey
        Distance To Prey > Smell Range -> Smell Prey -> 0
        Smell Prey & !Feel Secure ~> Wander -> Flee
        Smell Prey & Feel Secure ~> Wander -> Hunt
    !Mindset.Feel Secure & !Mindset.Smell Prey & Health.Hurt ~> Activity.Flee -> Activity.Recover
    * ~> Activity.Wander
    * ~> Health.Ok
    * ~@ Turns Wounded = 0
    <Stab> ~> Health.Hurt -> Health.Dead
    <Stab> ~> Health.Ok -> Health.Hurt
    Activity.Recover ~> Health.Hurt -> Health.Ok
    Health.Hurt & <Turn Ended> ~@ Turns Wounded += 1
    Health.Hurt ~> Mindset.Feel Secure -> %{10} -> Mindset.Feel Secure
    Health.Hurt ~> Mindset.Feel Secure -> %{Turns Wounded} -> 0
    Health.Ok & <Turn Ended> ~> Turns Wounded > 0 ~@ Turns Wounded -= 1
    Mindset.* & Health.Ok ~> Mindset.Feel Secure
    Mindset.Near Prey & !Mindset.Feel Secure ~> Activity.Attack -> Activity.Flee
    Mindset.Near Prey & Mindset.Feel Secure ~> Activity.Hunt -> Activity.Attack

---
Activity.Recover: {-8375573240400226964}
Health.Hurt: {-8461265714844041920}
Wumpus.Activity.Recover: {2339794052190335941}
Wumpus.Health.Ok: {1,211200070331592942}
