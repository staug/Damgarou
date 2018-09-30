from entity.gameentity import GameEntity, WanderingAIEntity


class FriendlyEntity(GameEntity):

    def __init__(self, name, position, image_ref=None):

        if not image_ref:
            image_ref = "HUMANOID_1"

        GameEntity.__init__(self, name=name, pos=position, image_ref=image_ref, z_level=2, blocks=True,
                            ai=WanderingAIEntity(speed=10))


class Fighter(FriendlyEntity):

    def __init__(self, position, image_ref=None):
        FriendlyEntity.__init__(self, "Fighter", position, image_ref=image_ref)

        self.attack = 10
        self.protection = 10

        self.wage_base = 5
