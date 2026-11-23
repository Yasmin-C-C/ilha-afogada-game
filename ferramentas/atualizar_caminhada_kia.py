"""Instala as duas folhas de caminhada aprovadas e reconstrói o atlas da Kia."""
import argparse
import json
import os
import shutil
import sys
from statistics import median
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import pygame
from PIL import Image

from characters.kia import PASTA_ANIMACOES


def instalar(fontes):
    pasta = PASTA_ANIMACOES
    backup = pasta / 'arquivo-caminhada-v1'
    if not backup.exists():
        backup.mkdir()
        shutil.copy2(pasta / 'animacoes.json', backup / 'animacoes.json')
        for versao in ('sem', 'com'):
            acao = f'caminhada-{versao}-espada'
            shutil.copytree(pasta / acao, backup / acao)
            shutil.copy2(pasta / ('folha-' + acao + '.png'), backup / ('folha-' + acao + '.png'))
    dados = json.loads((pasta / 'animacoes.json').read_text(encoding='utf-8'))
    for versao, fonte in zip(('sem', 'com'), fontes):
        acao = f'caminhada-{versao}-espada'
        folha = Image.open(fonte).convert('RGBA')
        shutil.copy2(fonte, pasta / ('folha-' + acao + '.png'))
        for linha, direcao in enumerate(('frente', 'costas', 'esquerda', 'direita')):
            faixa = folha.crop((0, round(linha * folha.height / 4), folha.width,
                                round((linha + 1) * folha.height / 4)))
            superficie = pygame.image.frombytes(faixa.tobytes(), faixa.size, 'RGBA')
            partes = sorted((r for r in pygame.mask.from_surface(superficie, 220).get_bounding_rects()
                             if r.width * r.height > 1000), key=lambda r: r.x)
            if len(partes) != 8:
                raise ValueError((acao, direcao, 'Esperados oito corpos completos', partes))
            altura_tronco = round(median(r.height for r in partes) * .56)
            # A guia mantém o quadril na mesma coluna; preservar esse registro
            # evita recentralizar o desenho em função da perna que avança.
            centros = []
            for i, r in enumerate(partes):
                topo_corpo = superficie.subsurface((r.x, r.y, r.width, round(r.height * .4)))
                centro_corpo = r.x + topo_corpo.get_bounding_rect(min_alpha=128).centerx
                centros.append(centro_corpo - (i + .5) * folha.width / 8)
            desvio_grade = median(centros)
            quadros = []
            for i, rect in enumerate(partes):
                rect.inflate_ip(12, 12)
                rect.clamp_ip(superficie.get_rect())
                corte = faixa.crop((rect.left, rect.top, rect.right, rect.bottom))
                quadro = Image.new('RGBA', (max(256, corte.width + 16), max(320, corte.height + 16)))
                quadro.paste(corte, ((quadro.width - corte.width) // 2, quadro.height - corte.height - 8))
                bbox = quadro.getchannel('A').point(lambda v: 255 if v >= 128 else 0).getbbox()
                x0, y0, x1, y1 = bbox
                # Registro do quadril na grade de poses, sem acompanhar as botas.
                y_quadril = y0 + altura_tronco
                origem_x = (quadro.width - corte.width) // 2
                x_quadril = round((i + .5) * folha.width / 8 + desvio_grade - rect.left + origem_x)
                arquivo = f'{acao}/{direcao}-{i + 1:02}.png'
                quadro.save(pasta / arquivo)
                quadros.append({'arquivo': arquivo, 'tamanho': list(quadro.size),
                                'limite_visivel': list(bbox),
                                'ancora_quadril': [x_quadril, y_quadril]})
            # As folhas frontais repetem cedo um apoio esquerdo no sexto desenho.
            # Reutilizar a transição do apoio direito equilibra a duração das pernas.
            # As duas passagens de costas usam a pose neutra, sem saltar de apoio.
            ordem = {'frente': (0, 1, 2, 3, 4, 3, 6, 7),
                     'costas': (0, 1, 2, 3, 4, 3, 2, 7)}.get(direcao, range(8))
            dados['animacoes'][acao]['direcoes'][direcao] = [quadros[i] for i in ordem]
        dados['animacoes'][acao]['distancia_ciclo'] = 72
        dados['animacoes'][acao]['alinhamento'] = 'quadril'
    (pasta / 'animacoes.json').write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding='utf-8')
    reconstruir_atlas()


def reconstruir_atlas():
    from characters.kia import carregar_animacoes_kia, assinatura_animacoes
    pygame.init()
    pygame.display.set_mode((1, 1))
    carregar_animacoes_kia.cache_clear()
    animacoes = carregar_animacoes_kia()
    total = sum(len(q) for ds in animacoes.values() for q in ds.values())
    atlas = pygame.Surface((192 * 10, 192 * ((total + 9) // 10)), pygame.SRCALPHA)
    indice, n = {}, 0
    for acao, ds in animacoes.items():
        indice[acao] = {}
        for direcao, quadros in ds.items():
            indice[acao][direcao] = []
            for quadro in quadros:
                r = quadro.get_rect(topleft=((n % 10) * 192, (n // 10) * 192))
                atlas.blit(quadro, r)
                indice[acao][direcao].append(list(r))
                n += 1
    dados = json.loads((PASTA_ANIMACOES / 'animacoes.json').read_text(encoding='utf-8'))
    pygame.image.save(atlas, str(PASTA_ANIMACOES / 'atlas-jogo.png'))
    (PASTA_ANIMACOES / 'atlas-jogo.json').write_text(json.dumps({
        'assinatura': assinatura_animacoes(dados), 'animacoes': indice}), encoding='utf-8')
    print(total, 'quadros no atlas, caminhada substituída')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sem_espada', type=Path)
    parser.add_argument('com_espada', type=Path)
    args = parser.parse_args()
    instalar((args.sem_espada, args.com_espada))
