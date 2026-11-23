import pygame


def desenhar_mar(tela, camera):
    tela.fill((23, 64, 74))
    dx, dy = getattr(camera, 'origem_mar', (0, 0))
    esquerda, topo = camera.x + dx, camera.y + dy
    for y in range(topo // 30 * 30, topo + tela.get_height(), 30):
        for x in range(esquerda // 100 * 100 - 100, esquerda + tela.get_width(), 100):
            inicio = x + (y // 30 % 3) * 17 - esquerda
            pygame.draw.line(tela, (40, 84, 94), (inicio, y - topo),
                             (inicio + 21, y - topo), 2)
