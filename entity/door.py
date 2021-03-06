from entity.gameentity import GameEntity, ActionableEntity


class Door(GameEntity):

    def __init__(self, position, door_type, closed=True):
        assert door_type in ("H", "V"), "Door type must be H or V and was found {}".format(door_type)

        image_ref = "DOOR_" + door_type

        self.closed = closed
        if closed:
            image_ref += "_CLOSED"

        if closed:
            GameEntity.__init__(self, pos=position, image_ref=image_ref, z_level=1, blocks=True,
                                actionable=ActionableEntity(radius=0,
                                                            actionable_by_player_only=True,
                                                            function=open_door))
        else:
            GameEntity.__init__(self, pos=position, image_ref=image_ref, z_level=1)


def open_door(door_entity, entity_that_triggers):
    print("{} passed a door at {}, was it closed: {}".format(entity_that_triggers, door_entity.pos, door_entity.closed))
    door_entity.update_graphics(door_entity.image_ref[0:7] + "OPEN")
    door_entity.actionable = None
    door_entity.blocks = False
