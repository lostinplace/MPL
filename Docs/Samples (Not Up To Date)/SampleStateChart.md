# Character

## Exists

When *spawned*, a *Character* *Exists*

While a *Character* *Exists*, it can be:
* **Dead**
* **Alive**
* **Equipped**

A *Character* cannot be both **Alive** and **Dead** at the same time

When a *Character* *dies*, it is **Dead**

### Alive

While a *Character* is **Alive**, it **Needs Food**

#### Needs Food

While a *Character* **needs food**, it can be either:
* **Ok**
* **Hungry**
* **Starving**

When a *Character* first **needs food**, it's `hunger` is set to 0

While a *Character* has `hunger <= HungryThreshold` it is **Ok**

Every *tick* while a *Character* is **hungry**, it's `hunger` is set to `ProcessCharacterHunger(Hunger:int, value)`

When a *Character* is **ok**, and it's `hunger > HungryThreshold`, the **character** becomes **hungry**

When a *Character* is **ok**, and it's `hunger > StarvationThreshold`, the **character** is **starving**

Every 500 seconds while the *Character* is **starving** it *suffers organ damage*

When a *Character* is *fed, "a good meal"* it's `hunger` is set to `0`

While a *Character* is **hungry**, when a *Character* is *fed, `a decent meal`* it's `hunger` is set to `0`

While a *Character* is **starving**, when a *Character* is *fed, "a decent meal"* it's `hunger` is set to `HungryThreshold` and it is **hungry**

When a *Character* is *fed a ~meal~* it has **recently eaten** for 500 seconds
