Character: MACHINE
  suffers organ damage : EVENT
  spawned *-> Exists
  Exists: STATE
    ENTER -> Alive
    Dead: Living
    Alive: Living
    Equipped: STATE

    killed *-> Dead

    Alive:
      Needs Food: STATE
        Ok: Exclusive
        Hungry: Exclusive
        Starving: Exclusive

        ENTER -* hunger = 0

        hunger <= HungryThreshold ~> Ok

        tick *-* hunger = `ProcessCharacterHunger(hunger:int, _.value:int)`
        hunger > HungryThreshold ~> Ok -> Hungry
        hunger > StarvationThreshold ~> Starving

        Every 500 Seconds *? Starving -* suffers organ damage

        fed a good meal *-* hunger = 0

        fed a decent meal *-> ?
          ! Hungry -> hunger = 0
          ! Starving -> hunger = HungryThreshold

        fed a /(.*)/meal *-> Recently Eaten
