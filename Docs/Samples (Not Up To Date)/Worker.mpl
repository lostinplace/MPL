Worker: MACHINE
    Maintenance: Activity
    Work: Activity
        Needs Focus: STATE
        Assigned(:string): STATE
        Focused(:string): Exclusive

        Assign(task_id:string, work_needed: int) *-> Progress[task_id] = 0;
                                                    RequiredWork[task] = work_needed ->
                                                    Assigned(task)

        !Focused -* Needs Focus ->> 500s *-> Work -> Maintenance

        Needs Focus -> Selected Task = `SelectTask(Assigned:[string], Desire:{string:int}):string` -> Focused(SelectedTask)

        Focused(task) ~> At Workstation ->> 300ms -> Progress(task) += 1

        Progress(Selected Task) >= Required Work[Selected Task] -* Work Done(Selected Task) -> \
            Progress(Selected Task) /-> Assigned(Selected Task) /-> Focus(Selected Task) /-> false

        Work Done(task) *-* Selected Task = None *-* Reward(task, 1)

        Reward(task, value) *-> Desire[task] += value


