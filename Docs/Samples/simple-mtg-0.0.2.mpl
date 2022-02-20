Player: machine
    Life: state
        Alive
        Dead
        * -> Alive

    Turn: state
        Not My Turn
        My Turn

    <Turn Assigned> this -> My Turn
    <Turn Assigned> !this -> Not My Turn

    * -> Life = 20

    <Damage> self $amount -@ Life -= $amount
    Life < 0 -> Dead

    Bank = 0

    <Upkeep> -> Bank = 0


Card: machine
    Location: state
        Deck
        Graveyard
        Hand
        In Play

    Activation: state
        Untapped
        Tapped


    * -@ Any Color === {`Red`|`Black`|`White`|`Green`|`Blue`}

    Uncolored Conversion =#= Any Color <=> `Uncolored`

    Can Pay =#= $Player, $Cost -@ $Player#Bank -= $Cost -> %{Uncolored Conversion} -> $Player#Bank > 0

    Played =#= <play> this, $player:Player -> Hand -@ Can Pay($player, Deploy Cost) -> In Play & Untapped

    <Played> -@ Owner = $player

    Activated =#= <Activate> this, $source:Player, $target -> Untapped -> Can Pay($source, Activation Cost) -> Tapped

    <Destroy> this -> Untapped & Graveyard

    <Untap Phase> -> Tapped -> Untapped


Mountain: Card
    <Activated> this, $source:Player -> $source#Bank += 1*`Red`


Lightning Bolt: Card
    * -@ Deploy Cost = `Red` + `Uncolored`
    <Activated> this, $target:Player -@ <Damage> $target, 3
    <Activated> this, $target:Card -@ <Destroy> $target
