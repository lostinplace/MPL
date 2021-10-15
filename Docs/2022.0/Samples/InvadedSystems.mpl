Vessel: MACHINE
    ENTER -> ACTIVE
    Active: Activity
    Destroyed: Activity
    Destroyed -> 5p -> DESTROY

    Core Destroyed *-> Active -> Destroyed

    Theater: MACHINE {PRODUCES:[Occupation/Occupied] }
    
    Active & !Theater/Occupation/Occupied ~> 4h -* Establish Base


Base: MACHINE
    ENTER -> Constructing
    Constructing: Activity
    Active: Activity
    Destroyed: Activity
    Destroyed -> 5p -> DESTROY

    Theater: CONNECTION {SRC: Theater, EXPOSES:[Assets]}

    Core Destroyed *-> Active | Constructing -> Destroyed
    Constructing -> 4h -> Active

    Active ~> 1h -* Do Work
    Do Work -* Theater HAS 0 Assets {SRC: Vessel} -> Create Vessel For Theater


Theater: MACHINE
    ENTER -> Inactive
    Inactive: Occupation
    Occupied: Occupation

    Assets: CONNECTION {SRC: Vessel|Base, EXPOSED:[Theater]}
    Neighbors: CONNECTION {SRC: Theater, PRODUCES:[Occupation/*], EXPOSES:[Assets]}

    Assets.Establish Base {SRC:Vessel} *- ADD VALUE to Assets -> Occupied

    Occupied ~> 8h -* Occupied Day -> inactive neighbor {TMP} = RESERVE 1 Neighbors {FUNCTION: SelectNeighbor}
        |-> inactive neighbor -* Occupation Target Identified(inactive neighbor)

    Occupation Target Identified {ALIAS: target} *-@  transfer possible {TMP} = CAN TRANSFER 1 Assets {SRC: Vessel} to target[Assets]
        |-> transfer possible -@ TRANSFER 1 Assets {SRC: Vessel} TO target[Assets] -* Ship Transferred From {THIS} to {target}
        |-> !transfer possible -* No Ships to Transfer(target)



