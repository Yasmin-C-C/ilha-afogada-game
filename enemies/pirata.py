from enemies.skeleton import Skeleton


class Pirata(Skeleton):
    sprite_nome = 'pirata'

    def __init__(self, x, y, patrulha=None):

        super().__init__(
            x,
            y,
            "centro",
            False,
            patrulha
        )

        # mais forte que Skeleton
        self.vida = 6
        self.detected = 240
        self.dist_ataque = 50
        self.cooldown = 800


