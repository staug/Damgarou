from utilities import MName, roll
import random

"""
A fighter is a booster to the player. It doesn't have a graphical representation...
"""


class Fighter:
    """
    Fighters live in fighter  guild,  unless they are part of the player suite
    """

    def __init__(self, fighter_dict={}):
        self.inventory = fighter_dict.get("Inventory", [])
        self.equipment = fighter_dict.get("Equipment", [])

        self.name = fighter_dict.get("Name", MName.person_name())
        self.gender = fighter_dict.get("Gender", random.choice(("Male", "Female", "Other")))
        self.race = fighter_dict.get("Race", random.choice(("Human", "Dwarf", "Elf", "Hobbit")))

        self.friendship = fighter_dict.get("Friendship",
                                           roll(6, 3))  # more or less friends, impact the loyalty of the group
        self.strength = fighter_dict.get("Strength", roll(6, 3))  # capable of carrying more objects

        self.money = random.randint(10, 200)
        self.food_level = 0

        self.age = 20
