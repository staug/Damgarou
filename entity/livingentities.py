from entity.gameentity import GameEntity, WanderingAIEntity


class FriendlyEntity(GameEntity):

    def __init__(self, name, position):

        image_ref = "HUMANOID_1"

        GameEntity.__init__(self, name=name, pos=position, image_ref=image_ref, z_level=2, blocks=True,
                            ai=WanderingAIEntity(speed=10))
