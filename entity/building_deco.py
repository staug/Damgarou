from entity.gameentity import GameEntity


class MuralLamp(GameEntity):

    def __init__(self, position, lamp_type="1"):
        image_ref = "MURAL_LAMP_" + lamp_type
        GameEntity.__init__(self, pos=position, image_ref=image_ref, z_level=1)
