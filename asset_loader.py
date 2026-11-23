"""Carregamento de imagens relativo ao projeto, compartilhado entre entidades."""
from functools import lru_cache
from pathlib import Path

import pygame

ASSETS = Path(__file__).resolve().parent / 'assets'


@lru_cache(maxsize=None)
def _carregar_original(nome):
    return pygame.image.load(str(ASSETS / nome)).convert_alpha()


@lru_cache(maxsize=None)
def carregar_imagem(nome, tamanho=None, rotacao=0):
    imagem = _carregar_original(nome)
    if rotacao:
        imagem = pygame.transform.rotate(imagem, rotacao)
    if tamanho is not None:
        escala = min(tamanho[0] / imagem.get_width(), tamanho[1] / imagem.get_height())
        dimensoes = (max(1, round(imagem.get_width() * escala)),
                     max(1, round(imagem.get_height() * escala)))
        ajustada = pygame.transform.smoothscale(imagem, dimensoes)
        imagem = pygame.Surface(tamanho, pygame.SRCALPHA)
        imagem.blit(ajustada, ((tamanho[0] - dimensoes[0]) // 2,
                              tamanho[1] - dimensoes[1]))
    return imagem


@lru_cache(maxsize=128)
def carregar_sprite_recortado(nome, tamanho):
    """Enquadra sprites com margens transparentes, preservando a proporção e o alfa."""
    original = _carregar_original(nome)
    limite = original.get_bounding_rect(min_alpha=8)
    quadro = pygame.Surface(tamanho, pygame.SRCALPHA)
    if not limite.width or not limite.height:
        return quadro
    visivel = original.subsurface(limite)
    escala = min(tamanho[0]/limite.width, tamanho[1]/limite.height)
    reduzida = pygame.transform.smoothscale(visivel, (
        max(1,round(limite.width*escala)), max(1,round(limite.height*escala))))
    quadro.blit(reduzida,reduzida.get_rect(midbottom=(tamanho[0]//2,tamanho[1])))
    return quadro


