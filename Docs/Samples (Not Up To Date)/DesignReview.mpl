DesignReview: MACHINE
    I See A Problem: STATE
    I See A Problem -> Problem Statement
    Problem Statement: STATE
        ENTER -> Write Problem Statement
        Finished Problem Statement Draft(url) *-> Problem Statement URL = url \
            /a-> Write Problem Statement -> Problem Statement Draft
            /b-> /DesignReview/PS Review/Team Review

    PS Review: STATE
        Team Review: STATE
            Needs Scheduling: STATE
            Scheduled(date:date): EVENT
            ENTER -> Needs Scheduling
            PS Team Review Scheduled(date:date) *-> PS Team Review Date = date -> Needs Scheduling -> Scheduled



    Design: STATE
    Design Review: STATE
    Finished: STATE



