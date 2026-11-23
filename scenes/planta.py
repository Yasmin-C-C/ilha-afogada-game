"""Contornos irregulares determinísticos dos cenários."""
import random

import pygame


def contorno_irregular(pontos, amplitude=16, passo=64):
    aleatorio = random.Random(31)
    contorno = []
    for a, b in zip(pontos, pontos[1:] + pontos[:1]):
        inicio, fim = pygame.Vector2(a), pygame.Vector2(b)
        distancia = inicio.distance_to(fim)
        if not distancia:
            continue
        normal = (fim-inicio).normalize().rotate(90)
        quantidade = max(1, round(distancia / passo))
        for i in range(quantidade):
            desvio = 0 if i == 0 else aleatorio.uniform(-amplitude, amplitude)
            ponto = inicio.lerp(fim, i / quantidade) + normal * desvio
            contorno.append((round(ponto.x), round(ponto.y)))
    return tuple(contorno)
