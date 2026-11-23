"""Quadros compartilhados, alinhados pelos pés e prontos para desenhar."""
import json
import hashlib
from functools import lru_cache

import pygame

from asset_loader import ASSETS


DIRECOES = {'baixo': 'frente', 'cima': 'costas',
            'esquerda': 'esquerda', 'direita': 'direita'}
TAMANHO = (288, 166)
ANCORA_X = 144


def assinatura_animacoes(pasta, dados):
    digest = hashlib.sha256(json.dumps(dados, sort_keys=True).encode('utf-8'))
    digest.update(b'inimigos-alinhamento-v1')
    for info in dados['animacoes'].values():
        for quadros in info['direcoes'].values():
            for quadro in quadros:
                stat = (pasta / quadro['arquivo']).stat()
                digest.update(f'{quadro["arquivo"]}:{stat.st_size}:{stat.st_mtime_ns}'.encode())
    return digest.hexdigest()


@lru_cache(maxsize=2)
def carregar_animacoes(nome):
    pasta = ASSETS / 'enemies' / (nome + '-animado')
    dados = json.loads((pasta / 'animacoes.json').read_text(encoding='utf-8'))
    indice = pasta / 'atlas-jogo.json'
    if indice.is_file() and (pasta / 'atlas-jogo.png').is_file():
        atlas_info = json.loads(indice.read_text(encoding='utf-8'))
        if atlas_info.get('assinatura') == assinatura_animacoes(pasta, dados):
            atlas = pygame.image.load(str(pasta / 'atlas-jogo.png')).convert_alpha()
            return {acao: {direcao: [atlas.subsurface(pygame.Rect(rect)) for rect in quadros]
                           for direcao, quadros in direcoes.items()}
                    for acao, direcoes in atlas_info['animacoes'].items()}
    animacoes = {}
    for acao, info in dados['animacoes'].items():
        animacoes[acao] = {}
        for direcao, quadros in info['direcoes'].items():
            referencia = quadros[-1] if acao in ('ataque', 'dano') else quadros[0]
            limite = referencia['limite_visivel']
            escala = 110 / (limite[3] - limite[1])
            imagens = []
            for quadro in quadros:
                original = pygame.image.load(str(pasta / quadro['arquivo'])).convert_alpha()
                x, y, direita, fundo = quadro['limite_visivel']
                visivel = original.subsurface((x, y, direita - x, fundo - y))
                if acao == 'derrota':
                    centro = visivel.get_width() / 2
                else:
                    faixa = pygame.Rect(0, int(visivel.get_height() * .84), visivel.get_width(),
                                        visivel.get_height() - int(visivel.get_height() * .84))
                    pes = visivel.subsurface(faixa).get_bounding_rect(min_alpha=128)
                    centro = pes.centerx if pes.width else visivel.get_width() / 2
                tamanho = (max(1, round(visivel.get_width() * escala)),
                           max(1, round(visivel.get_height() * escala)))
                reduzida = pygame.transform.smoothscale(visivel, tamanho)
                imagem = pygame.Surface(TAMANHO, pygame.SRCALPHA)
                destino = (ANCORA_X - round(centro * escala), TAMANHO[1] - tamanho[1])
                if destino[0] < 0 or destino[0] + tamanho[0] > TAMANHO[0] or destino[1] < 0:
                    raise ValueError(f'Quadro excede a margem: {nome}/{quadro["arquivo"]}')
                imagem.blit(reduzida, destino)
                imagens.append(imagem)
            animacoes[acao][direcao] = imagens
    return animacoes


@lru_cache(maxsize=4)
def carregar_animacoes_escaladas(nome, altura):
    base = carregar_animacoes(nome)
    if altura == 110:
        return base
    fator = altura / 110
    return {acao: {direcao: [pygame.transform.smoothscale(imagem,
                           (round(imagem.get_width() * fator), round(imagem.get_height() * fator)))
                           for imagem in quadros]
                   for direcao, quadros in direcoes.items()}
            for acao, direcoes in base.items()}


def salvar_atlas(nome):
    pasta = ASSETS / 'enemies' / (nome + '-animado')
    animacoes = carregar_animacoes(nome)
    atlas = pygame.Surface((TAMANHO[0] * 8, TAMANHO[1] * 11), pygame.SRCALPHA)
    indice, contador = {}, 0
    for acao, direcoes in animacoes.items():
        indice[acao] = {}
        for direcao, quadros in direcoes.items():
            indice[acao][direcao] = []
            for quadro in quadros:
                rect = quadro.get_rect(topleft=((contador % 8) * TAMANHO[0], (contador // 8) * TAMANHO[1]))
                atlas.blit(quadro, rect)
                indice[acao][direcao].append(list(rect))
                contador += 1
    pygame.image.save(atlas, str(pasta / 'atlas-jogo.png'))
    dados = json.loads((pasta / 'animacoes.json').read_text(encoding='utf-8'))
    (pasta / 'atlas-jogo.json').write_text(json.dumps({
        'assinatura': assinatura_animacoes(pasta, dados), 'animacoes': indice}), encoding='utf-8')
