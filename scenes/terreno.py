from asset_loader import carregar_imagem
import math
import random

import pygame


COR_AREIA = (210, 170, 100)


def faixa_irregular(caminho, largura, amplitude=8, passo=24, semente=7):
    """Margens orgânicas estáveis no mundo, com uma faixa central transitável."""
    centros = []
    for a, b in zip(caminho, caminho[1:]):
        inicio, fim = pygame.Vector2(a), pygame.Vector2(b)
        quantidade = max(1, math.ceil(inicio.distance_to(fim) / passo))
        centros.extend(inicio.lerp(fim, i / quantidade) for i in range(quantidade))
    centros.append(pygame.Vector2(caminho[-1]))
    fase = random.Random(semente).uniform(0, math.tau)
    esquerda, direita = [], []
    for i, centro in enumerate(centros):
        tangente = centros[min(i + 1, len(centros) - 1)] - centros[max(0, i - 1)]
        if not tangente.length_squared():
            continue
        normal = tangente.normalize().rotate(90)
        for lado, borda in ((1, esquerda), (-1, direita)):
            variacao = amplitude * (.6 * math.sin(i * .43 + fase + lado)
                                    + .4 * math.sin(i * .17 + fase * lado))
            ponto = centro + normal * lado * max(0, largura / 2 + variacao)
            borda.append((round(ponto.x), round(ponto.y)))
    return tuple(esquerda + list(reversed(direita)))


def desenhar_pedras_pequenas(tela, camera, pedras):
    for rect in pedras:
        tela.blit(carregar_imagem('objects/pedra.png', rect.size), camera.rect(rect))
