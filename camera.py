class Camera:
    def __init__(self, tela_x, tela_y, mapa_x, mapa_y):
        self.x = 0
        self.y = 0

        self.tela_x = tela_x
        self.tela_y = tela_y

        self.mapa_x = mapa_x
        self.mapa_y = mapa_y
        self.min_x = 0

    def update(self, alvo):
        self.x = alvo.centerx - self.tela_x // 2
        self.y = alvo.centery - self.tela_y // 2

        self.x = max(self.min_x, self.x)
        self.y = max(0, self.y)

        self.x = min(
            self.x,
            self.mapa_x - self.tela_x
        )

        self.y = min(
            self.y,
            self.mapa_y - self.tela_y
        )


    def rect(self, rect):

        return rect.move(
            -self.x,
            -self.y
        )


    def pos(self, x, y):

        return (
            x - self.x,
            y - self.y
        )
