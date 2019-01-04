"""
Small test for basic rpg ruleset
"""
from dataclasses import dataclass, field
import utilities
import random


@dataclass
class Character:
    name: str = None

    strength: int = 0
    dexterity: int = 0
    constitution: int = 0
    intelligence: int = 0
    wisdom: int = 0
    charisma: int = 0

    # race: str = random.choice(('Human', 'Dwarf', 'Elf', 'Halfling'))
    race: str = 'Human'
    classe: str = "Fighter"

    xp: int = 0
    money: int = 0
    original_hit_point: int = 0
    current_hit_points: int = 0
    equipment: dict = field(default_factory=dict)
    level: int = 1

    def __post_init__(self):
        # Roll attributes
        if self.strength == 0:
            self.strength = utilities.roll(6, 3)
        if self.dexterity == 0:
            self.dexterity = utilities.roll(6, 3)
        if self.constitution == 0:
            self.constitution = utilities.roll(6, 3)
        if self.intelligence == 0:
            self.intelligence = utilities.roll(6, 3)
        if self.wisdom == 0:
            self.wisdom = utilities.roll(6, 3)
        if self.charisma == 0:
            self.charisma = utilities.roll(6, 3)

        if self.money == 0:
            self.money = utilities.roll(6, 3) * 10

        if self.original_hit_point == 0:
            self.original_hit_point = utilities.roll(8)

        self.original_hit_point = max(1, self.original_hit_point + self.modifier_constitution)
        self.current_hit_point = self.original_hit_point
        self.equipment["armor"] = random.choice(['None', 'Leather', 'Chain', 'Mail'])
        self.equipment["shield"] = random.choice(['None', 'Shield'])
        self.equipment["weapon"] = random.choice(['Shortsword', 'Longsword'])
        if not self.name:
            self.name = utilities.MName.person_name()

    def is_valid_fighter(self):
        return self.strength >= 9

    def roll_initiative(self):
        return utilities.roll(6) + self.modifier_dexterity

    @property
    def armor_class(self):
        return 11

    def compute_damage(self):
        # for 1d6+2, return the result of [1, 6, 2] -> this is what is stored in the weapon
        return utilities.roll(6) + 2 + self.modifier_strength

    @property
    def modifier_strength(self):
        return Character._modifier_table(self.strength)

    @property
    def modifier_dexterity(self):
        return Character._modifier_table(self.dexterity)

    @property
    def modifier_constitution(self):
        return Character._modifier_table(self.constitution)

    @property
    def modifier_intelligence(self):
        return Character._modifier_table(self.intelligence)

    @property
    def modifier_wisdom(self):
        return Character._modifier_table(self.wisdom)

    @property
    def modifier_charisma(self):
        return Character._modifier_table(self.charisma)

    @staticmethod
    def _modifier_table(value):
        table = [-3, -3, -3, -3, -2, -2, -1, -1, -1, 0, 0, 0, 0, 1, 1, 1, 2, 2, 3]
        if value > 18:
            return 3
        return table[value]

    @property
    def attack_bonus(self):
        return (0, 1, 2, 2, 3, 4, 4, 5, 6, 6, 6, 7, 7, 8, 8, 8, 9, 9, 10, 10, 10)[self.level]


@dataclass
class Monster:
    # Values from external
    name: str
    armor_class: int
    hit_dice: tuple = field(default_factory=tuple)  # (X, Y) = Xd8 + Y
    attacks: dict = field(default_factory=dict)  # dict of attack name, int value
    damage_list: dict = field(default_factory=dict)  # dict of attack_name: (X, Y, Z) (attackname: 3d6+4)
    movement: int = 0
    morale: int = 0
    save_as: tuple = field(default_factory=tuple)  # tuple: (Class, Level)
    treasure_type: str = 'H'
    experience: int = 0

    # Default
    attacks_operator: str = "AND"

    # For combat
    modifier_strength: int = 0
    modifier_dexterity: int = 0

    def __post_init__(self):
        self.current_hit_point = utilities.roll(8, self.hit_dice[0]) + self.hit_dice[1]
        return

    def roll_initiative(self):
        return utilities.roll(6)

    @property
    def attack_bonus(self):
        if self.hit_dice[0] >= 32:
            return 16
        return [0, 1, 2, 3, 4, 5, 6, 7, 8, 8, 9, 9, 10, 10,
                11, 11, 12, 12, 12, 12, 13, 13, 13, 13, 14,
                14, 14, 14, 15, 15, 15, 15][self.hit_dice[0]]

    def compute_damage(self):
        if self.attacks_operator != "AND":
            current_weapon = random.choice(self.attacks.keys())
            print("Attacking with " + current_weapon)
            return utilities.roll(self.attacks[current_weapon][1],
                                  self.attacks[current_weapon][0]) + self.attacks[current_weapon][2]
        else:
            total = 0
            print("Attacking with " + str(self.attacks.keys()))
            for weapon in self.attacks.keys():
                total += (utilities.roll(self.damage_list[weapon][1], self.damage_list[weapon][0]) +
                          self.damage_list[weapon][2]) * self.attacks[weapon]
            return total


def combat_round(opponents_groups):
    print(opponents_groups)

    opponents = []
    for op_group in opponents_groups:
        opponents.extend(op_group)
    # Roll initiative and order opponents
    initiative = {}
    for i in range(len(opponents)):
        result = opponents[i].roll_initiative()

        if result in initiative.keys():
            initiative[result].append(opponents[i])
        else:
            initiative[result] = [opponents[i]]

    sorted_keys = []
    for key in initiative.keys():
        sorted_keys.append(key)
    sorted_keys.sort(reverse=True)

    opponents_sorted = []
    for key in sorted_keys:
        opponents_sorted.extend(initiative[key])

    # Start the battles
    dead_list = []

    for current_fighter in opponents_sorted:
        if current_fighter not in dead_list:
            print("Now is the turn of " + current_fighter.name)
            # recovering the group of allies
            allied_group = None
            for group in opponents_groups:
                if current_fighter in group:
                    allied_group = group
                    break
            # Quick check: is there anybody left to battle?
            possible_adversaries = []
            for entity in opponents_sorted:
                if entity not in dead_list and entity not in allied_group:
                    possible_adversaries.append(entity)

            # finding an adversary
            adversary = None
            if len(possible_adversaries) > 0:
                adversary = random.choice(possible_adversaries)

            if adversary:
                print("He is fighting " + adversary.name)

                roll = utilities.roll(20)
                print("Roll: {}, attack_bonus:{}, modifier_str: {}, Adversary AC {}".format(roll,
                                                                                            current_fighter.attack_bonus,
                                                                                            current_fighter.modifier_strength,
                                                                                            adversary.armor_class))
                if roll == 1:
                    print("BIG Failure")
                elif roll == 20 or roll + current_fighter.attack_bonus + current_fighter.modifier_strength >= adversary.armor_class:
                    damage = current_fighter.compute_damage()
                    print("DAMAGE, rolling hits " + str(damage))
                    adversary.current_hit_point -= damage
                    if adversary.current_hit_point <= 0:
                        print("DEAD:" + adversary.name)
                        dead_list.append(adversary)
                else:
                    print("Failure")

    # Now we remove all the dead
    for group in opponents_groups:
        for opponent in group:
            if opponent in dead_list:
                group.remove(opponent)


if __name__ == '__main__':

    monster = Monster(name="Faun",
                      armor_class=15,
                      hit_dice=(1, 0),
                      attacks={"miniature weapon": 1},
                      damage_list={"miniature weapon": (1, 6, 0)},
                      movement=40,
                      save_as=("Fighter", 1),
                      morale=8,
                      treasure_type="D",
                      experience=25)
    print(monster)

    group1 = [Character(name="A1"), Character(name="A2"), Character(name="A3")]
    group2 = [monster, Character(name="B1")]
    i = 1;
    while len(group1) > 0 and len(group2) > 0:
        print("ROUND NUMBER ---- " + str(i))
        combat_round((group1, group2))
        print("Remain  in group1  {} and  in group2 {}".format(len(group1), len(group2)))
        i += 1
        print()
        print()
