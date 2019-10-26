from entity.gameentity import GameEntity, WanderingAIEntity
from utilities import MName, roll
import random

class FriendlyEntity(GameEntity):

    def __init__(self, name, position, image_ref=None):

        if not image_ref:
            image_ref = "HUMANOID_1"

        GameEntity.__init__(self, name=name, pos=position, image_ref=image_ref, z_level=2, blocks=True,
                            ai=WanderingAIEntity(speed=10))


class FighterEntity(FriendlyEntity):

    def __init__(self, name, position, image_ref=None, fighter_dict={}):
        FriendlyEntity.__init__(self, name, position, image_ref=image_ref)

        self.attack = 10
        self.protection = 10

        self.wage_base = 5

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
