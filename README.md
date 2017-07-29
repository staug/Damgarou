# Damgarou
Roguelike in Python and Pygame, centered around merchant and exchanges
Idea from roguebasin.

Synopsis:
The player is a young merchant ? a turn of fortune has pushed him to choose this carrier. He is travelling from town to town ? the passages from town to town are mostly via subterrans parts (which forms the dungeon), selling equipments. The dungeon also offers him the opportunity to loot enemies or discover treasure, but he has to be careful as he is ultra weak? He may also do quests (mainly carry object from point A to B) to earn more money and experience.

Game goal:
The game is time limited (X turns, configurable at the start). The player has to become the richest possible in this time limit. And survive. A turn is materialized by a town.

phase 2: game may be affected at teh beginning depending at HOW we want it to be played: nb of terms limited, exploration (with a set of quests)

Setup:
Initial screen: start new game, load game, options, exit.
Start new game -> player setup screen, then regular game.
Setup screen -> start with all random, possible to edit manually the figures

Rules:

Become richer
The base is to buy goods in some places, while selling them elsewhere. The number of slots a player has is limited ? in order to expand he has to hire some mules or buy some objects (better handbags for example). Each good takes x slot - if the player buys huge quantities the quantity can be spread across multiple, but the individual good cannot be split.
Resources
Two resources are to be managed:
?       Gold ? this is the basic trading quantity. Gold is decreased by taxes (each turn), by salary to allies, when losing battles (paying ranson), or by special events. Not being able to pay taxes will trigger bad events. Not being able to pay salary will trigger bad events (worst: the ally leaves the player)
Gold is increased by commerce, by interest in the bank, by special events

?       Food ? this is used to feed the player and the allies. Not having food triggers desertion from allies and bad events for the player. Food takes place in the inventory.
Food is increased in taverns and in special events. Food is decreased when feeding players/allies

Fighting
The player can equip object and hire allies (mercenaries or mules) to help him become richer. The player cannot fight by himself (except via using objects, bribing or casting spells)! He can only defend himself (parry). This is also true for the mules ? only the mercenaries will attack.
Fighting is a simple system to be defined. Fighting are automatically resolved, but at the end of each fighting turn the player will have the possibility to flee, with random consequence. If the fight is lost the player will have to pay a ranson using his bank account ? if no money in the bank then the party is finished.
Travelling
Each town is linked with a limited number of other towns. Travelling may take several turns, and one food ration is decreased by turn. The tavern may be used to know the type of towns nearby ? once the player has been in a town, its type is retained.
A way to view the town graph should be presented.
General entity stats:
* name
* race:
- help sell/buy from certain person
- prevent the buy from certain products (note that for mule, that means that they will refuse to carry the products)
- prevent the equipment of certain objects
* previous occupation: gives bonus on equipment? Allow to craft?
* charisma: gives bonus/malus to costs of sales, ability to bribe enemies
* friendship: gives more/less friends, impact the loyalty of the people in the group. A low
* objects: gives more/less objects slots
* food consumption [impacted by strength, inverse].
* exposure to elements: there are 4 elements (fire/earth/water/ether). Any person is always either immune to 2 and double penalized to 2, equally attached to 4 (no bonus/malus) or immune to 1, pealized by one and equal to 2.
* strength: gives more/less capacities to transport. More strength means more food is consumed!
* erudition level: able to detect usage of objects, getting more gold (unidentified object will have 1/10th of the value). More erudition means more arrogant, so charisma going down!
 [to buy/sell merchandise]
money level
inventory slots
[to survive]
health
protection
attack (this doesn?t exist for player, this is low by default as he is supposed to be a merchant!)
food level
[attached to the player]
object slots
friends slots
curse/benediction: player may be cursed/blessed (limited time, impact one/several attributes)

Friends:
friends are of two sorts: mercenaries and mules. They follow the exposure to elements.
mercenaries help attack/defend. they come fully equipped, you cannot modify their equipment. Some of them are magician, some pure warriors. They can be healed (cost money). They have a friendship level (the more friendly, the less powerful they are) which dictates their behaviour in case of lack of money (the more friendship teh less chance they could attack they could do to you in case of non payment)
mules simply carry the equipments. They cannot attack, can be healed (cost money). In case of death, all attached objects are lost!. They have a friendship level that says to which point they can go away. Note that the more powerful mule may simply decide to leave out of spite (1 out of 10 chance?)
friends cost money per travel. If not enouhg money:
- mercenaries may attack you (2 out of 3 chance, moduled by friendship level)
- mules may leave you (2 out of 3 chance, moduled by friendship level)
friends cost food per travel. If not enough food: friends will leave (20% chance after first travel, 30% after 2nd travel...; this counter can be reset with a salary increase which stayes forecver)

Objects:
each object has a weight, which impacts your personal number of what you can carry
weapons: modify your attack. can be used after a while.
armors: can be used after a while. modify your protection (base and/or on specific element(s))
revival potion [if you die, you still survive with only the money in the bank]
fridge: allow to store more food
spell scroll: attack on one element. Consumed after.
Objects may be crafted? This will be part of step 2.

Merchandise:
each merchandise has a price and a weight and a space factor.
some merchandise can only be bought/sold in certain type of town.

Town:
Travel between town costs food. How much?
Events may occure when travelling.
twon may undergo special condition that drives price up.
town have alignment that specifies the type of good that can be offered/sold.

Places in town:
[temple] -> Heal, remove curse, bless
[trading place] -> buy/sell
[shops] buy equipment, repair equipment(?), craft equipment(?)
[guild] hire friends.
[Tavern]: special missions(?) - take somebody to a place, ... & gossips on other towns. buy food.
[bank] store money/get money, interest. Money in accrues interests, but not all towns has a bank.
[special places]: depend on teh mission - could be simple maze exploration in later games?

[Town]
Town can be agricultural (20%), hunting  (20%), mining (20%), administrative (15%), military (15%) or outlaw (10%).

[Places in town]
Places in town depends mainly on the type of town. Chance below:
                  agricultural      | hunting         | mining          | administrative | military        | outlaw.
Market            90%               | 90%             | 90%             | 90%             | 80%            | 80%
Tavern            80%               | 80%             | 60%             | 50%             | 60%            | 70%
Shop              80%               | 80%             | 80%             | 60%             | 50%            | 50%
Temple            30%               | 20%             | 20%             | 60%             | 50%            | 10%
Bank              10%               | 10%             | 10%             | 80%             | 60%            |  0%
Guild (Fighter) 30%                | 30%             | 30%             | 10%             | 90%            | 90%
Guild (Mule)      40%               | 40%             | 70%             | 10%             | 50%            | 30%
An alogorithm should be applied to make sure that there is always 3 temples, 2 banks in the world

[Inventory]
Inventory holds goods as well as non equipped objects. Inventory is a property of the player as well as mules.
Each piece of inventory has a weight, and take up one slot. Only the player has slots for non equipped objects.

* Bargaining goods
Bargaining goods are only present in the inventory
Bargaining goods retain their original price to show the delta in price, as well as the town where they were bought
/later/ in some conditions (crafting skills) it is possible to assemble a set of bargaining goods to make an equipment(?)
Some bargaining goods are illegal in some town. If illegal goods are carried, then the police may happen (choice to fight, flee or bribe) at the town entrance. Illegal goods are only available in a given place.

Bargaining goods by town:
goods have a main category and a subtype (for fun only). The main category is the one that defines its supply/demand.
- agricultural town:
available:
food variety [+++]: cereals,
demand:
manufactured goods [---]
weapons [-]
slaves [---]
drug [-]

- hunting town:
available:
food [+++]: meat,
fur [+++]:
ore [+]:
jewel [+]:
demand:
weapon [--]:
drug [-]

- mining town:
available:
ore [+++]:
jewel [+++]:
food [+]
demand:
weapon [--]:
manufactured goods [--]

- administrative town:
demand:
fur [++]

- military town:

- outlaw town:

* Equipment
Non equipped objects can be equipped by the player or by the allies
When equipped, they don't take inventory slot but still carry their weight
One can equip only if there are equipment slots left
Any removed equipment has to be put in the inventory or in another ally (unless the player and his allies are in a shop), otherwise it is drop on teh floor and as such lost.
If an ally leaves willingly, its equipment must find its way in the player or in another ally (otherwise it is lost)
Race may prevent some equipment

-> method:
pickup(self) -> move the equipment to the player inventory
equip(self, player or ally) -> try to set the equipment. As race (and other) may prevent the equipment action, this is not always a given
unequip(self)
assign_to(self, player or ally) -> unequip then call the equip method
buy/sell(self)
destruct(self) -> transform the equipment into piece of bargaining goods.


****
Graphical Credits
This project uses Dawnlike tileset, from https://opengameart.org/content/dawnlike-16x16-universal-rogue-like-tileset-v181
