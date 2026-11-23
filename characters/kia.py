import json
import hashlib
from functools import lru_cache

import pygame

from asset_loader import ASSETS
from colisoes import bloqueia_movimento


PASTA_ANIMACOES = ASSETS / 'characters' / 'kia-nova'
DIRECOES = {'baixo': 'frente', 'cima': 'costas',
            'esquerda': 'esquerda', 'direita': 'direita'}
ANCORA = (96, 166)
DURACAO_ATAQUE = 350
INTERVALO_CAMINHADA_MS = 120
ALTURA_CORPO_KIA = 118


def assinatura_animacoes(dados):
    digest = hashlib.sha256(json.dumps(dados, sort_keys=True).encode('utf-8'))
    digest.update(b'kia-combate-anatomia-v6')
    for info in dados['animacoes'].values():
        for quadros in info['direcoes'].values():
            for quadro in quadros:
                stat = (PASTA_ANIMACOES / quadro['arquivo']).stat()
                digest.update(f'{quadro["arquivo"]}:{stat.st_size}:{stat.st_mtime_ns}'.encode())
    return digest.hexdigest()


@lru_cache(maxsize=1)
def carregar_animacoes_kia():
    """Carrega uma vez e mantém em memória apenas os quadros na escala do jogo."""
    dados = json.loads((PASTA_ANIMACOES / 'animacoes.json').read_text(encoding='utf-8'))
    indice = PASTA_ANIMACOES / 'atlas-jogo.json'
    if indice.is_file() and (PASTA_ANIMACOES / 'atlas-jogo.png').is_file():
        atlas_info = json.loads(indice.read_text(encoding='utf-8'))
        if atlas_info.get('assinatura') == assinatura_animacoes(dados):
            atlas = pygame.image.load(str(PASTA_ANIMACOES / 'atlas-jogo.png')).convert_alpha()
            return {acao: {direcao: [atlas.subsurface(pygame.Rect(rect)) for rect in quadros]
                           for direcao, quadros in direcoes.items()}
                    for acao, direcoes in atlas_info['animacoes'].items()}
    animacoes = {}
    for acao, info in dados['animacoes'].items():
        animacoes[acao] = {}
        for direcao, quadros in info['direcoes'].items():
            # Uma escala de referência preserva o tamanho ao agachar ou cair.
            referencia = quadros[-1] if acao.startswith(('ataque', 'esquiva', 'dano')) else quadros[0]
            imagens = []
            for quadro in quadros:
                # Quadros em pé têm a mesma altura corporal, sem contar a arma.
                em_pe = acao.startswith(('parada', 'caminhada', 'dano')) or acao == 'ataque'
                medida = quadro if em_pe else referencia
                limite = medida.get('limite_corpo', medida['limite_visivel'])
                escala = ALTURA_CORPO_KIA / (limite[3] - limite[1])
                if 'escala_corporal' in info:
                    # Uma escala anatômica por sequência, medida pela cabeça.
                    # Dobrar as pernas não aumenta cabeça, tronco ou espada.
                    escala = info['escala_corporal'][direcao]
                original = pygame.image.load(str(PASTA_ANIMACOES / quadro['arquivo'])).convert_alpha()
                rect = pygame.Rect(quadro['limite_visivel'])
                rect.width -= rect.x
                rect.height -= rect.y
                visivel = original.subsurface(rect)
                # Na caminhada, fixar o corpo lateralmente e manter o chão nos pés.
                # Não fixar o quadril em Y: isso fazia as botas flutuarem.
                if acao.startswith('caminhada'):
                    topo = visivel.subsurface((0, 0, visivel.get_width(),
                                                max(1, round(visivel.get_height() * .32))))
                    centro = topo.get_bounding_rect(min_alpha=128).centerx
                elif acao == 'derrota':
                    centro = visivel.get_width() / 2
                else:
                    faixa = pygame.Rect(0, round(visivel.get_height() * .84),
                                        visivel.get_width(), max(1, round(visivel.get_height() * .16)))
                    faixa.height = min(faixa.height, visivel.get_height() - faixa.y)
                    pes = visivel.subsurface(faixa).get_bounding_rect(min_alpha=128)
                    centro = pes.centerx if pes.width else visivel.get_width() / 2
                tamanho = (max(1, round(visivel.get_width() * escala)),
                           max(1, round(visivel.get_height() * escala)))
                reduzida = pygame.transform.smoothscale(visivel, tamanho)
                if 'calibracao_cabeca' in info:
                    calibracao = info['calibracao_cabeca'][direcao]
                    corpo = quadro.get('limite_corpo', quadro['limite_visivel'])
                    fim_cabeca = corpo[1] + calibracao['altura_cabeca_fonte']
                    corte = max(1, min(tamanho[1]-1, round((fim_cabeca-rect.y)*escala)))
                    inferior = reduzida.subsurface((0,corte,tamanho[0],tamanho[1]-corte))
                    altura_inferior = max(1, round(inferior.get_height()*calibracao['fator_corpo']))
                    corrigida = pygame.Surface((tamanho[0],corte+altura_inferior),pygame.SRCALPHA)
                    corrigida.blit(reduzida.subsurface((0,0,tamanho[0],corte)),(0,0))
                    corrigida.blit(pygame.transform.smoothscale(inferior,(tamanho[0],altura_inferior)),(0,corte))
                    reduzida = corrigida
                    tamanho = corrigida.get_size()
                image = pygame.Surface((192, 192), pygame.SRCALPHA)
                image.blit(reduzida, (ANCORA[0] - round(centro * escala),
                                     ANCORA[1] - tamanho[1]))
                imagens.append(image)
            animacoes[acao][direcao] = imagens
    return animacoes


class Kia:
    def __init__(self):
        self.x, self.y = 1580, 2200
        self.width, self.height = 30, 18
        self.speed = 2.6
        self.vida = 5
        self.viva = True
        self.rect = pygame.Rect(self.x + 16, self.y + 100, self.width, self.height)
        self.bodyRect = pygame.Rect(self.x + 10, self.y + 25, 42, 90)
        self.direcao = 'baixo'
        self.animacoes = carregar_animacoes_kia()
        self.reiniciar_animacoes()
        self.equipar_espada(False)

    def reiniciar_animacoes(self):
        self.inicio_ataque = -10000
        self.inicio_interacao = -10000
        self.inicio_dano = -10000
        self.inicio_derrota = None
        self.inicio_esquiva = -10000
        self.esquiva_ate = -10000
        self.ultima_movimentacao = -10000
        self.direcao_ataque = self.direcao
        self.direcao_esquiva = self.direcao
        self.animacao_atual = None
        self.inicio_animacao = pygame.time.get_ticks()
        self.quadro_atual = 0

    def equipar_espada(self, equipada=True):
        self.espada_equipada = equipada
        estado = 'parada-com-espada' if equipada else 'parada-sem-espada'
        self.image_frente = self.animacoes[estado]['frente'][0]
        self.image_costas = self.animacoes[estado]['costas'][0]
        self.image_esquerda = self.animacoes[estado]['esquerda'][0]
        self.image_direita = self.animacoes[estado]['direita'][0]
        self.image = self.animacoes[estado][DIRECOES[self.direcao]][0]

    def iniciar_interacao(self):
        if self.viva:
            self.inicio_interacao = pygame.time.get_ticks()

    def iniciar_esquiva(self, direcao, duracao):
        self.inicio_esquiva = pygame.time.get_ticks()
        self.esquiva_ate = self.inicio_esquiva + duracao
        self.inicio_interacao = -10000
        self.inicio_ataque = -10000
        self.direcao_esquiva = ('direita' if direcao.x > 0 else 'esquerda') if abs(direcao.x) > abs(direcao.y) else ('baixo' if direcao.y > 0 else 'cima')
        self.duracao_esquiva = duracao

    def ataque_ativo(self, agora):
        return self.viva and 80 <= agora - self.inicio_ataque < 180

    def visual(self, atacando=False):
        agora = pygame.time.get_ticks()
        direcao = self.direcao
        versao = 'com-espada' if self.espada_equipada else 'sem-espada'
        duracao = None
        if not self.viva:
            if self.inicio_derrota is None:
                self.inicio_derrota = agora
            acao, inicio, duracao = 'derrota', self.inicio_derrota, 1080
        elif agora < self.esquiva_ate:
            acao, inicio, duracao = 'esquiva-' + versao, self.inicio_esquiva, self.duracao_esquiva
            direcao = self.direcao_esquiva
        elif agora - self.inicio_dano < 240:
            acao, inicio, duracao = 'dano-' + versao, self.inicio_dano, 240
        elif agora - self.inicio_ataque < DURACAO_ATAQUE:
            acao, inicio, duracao = 'ataque', self.inicio_ataque, DURACAO_ATAQUE
            direcao = self.direcao_ataque
        elif agora - self.inicio_interacao < 300:
            acao, inicio, duracao = 'interacao', self.inicio_interacao, 300
        else:
            acao = ('caminhada-' if agora - self.ultima_movimentacao < 80 else 'parada-') + versao
            inicio = self.inicio_animacao
        estado = acao, direcao
        if self.animacao_atual != estado:
            self.animacao_atual = estado
            self.inicio_animacao = agora
            if duracao is None:
                inicio = agora
        quadros = self.animacoes[acao][DIRECOES[direcao]]
        if duracao:
            indice = min(len(quadros) - 1, max(0, (agora - inicio) * len(quadros) // duracao))
        else:
            intervalo = INTERVALO_CAMINHADA_MS if acao.startswith('caminhada') else 200
            indice = max(0, (agora - self.inicio_animacao) // intervalo) % len(quadros)
        self.quadro_atual = indice
        self.image = quadros[indice]
        return self.image, (self.x + 31 - ANCORA[0], self.y + 121 - ANCORA[1])

    def move(self, obstaculos, mapa_x, mapa_y):
        keys = pygame.key.get_pressed()
        movimentos = (
            (pygame.K_w, 0, -self.speed, 'cima', self.image_costas),
            (pygame.K_s, 0, self.speed, 'baixo', self.image_frente),
            (pygame.K_d, self.speed, 0, 'direita', self.image_direita),
            (pygame.K_a, -self.speed, 0, 'esquerda', self.image_esquerda),
        )
        for tecla, dx, dy, direcao, imagem in movimentos:
            if not keys[tecla]:
                continue
            self.direcao, self.image = direcao, imagem
            x = max(0, min(mapa_x - self.width - 16, self.x + dx))
            y = max(0, min(mapa_y - self.height - 100, self.y + dy))
            pes = pygame.Rect(x + 16, y + 100, self.width, self.height)
            corpo = pygame.Rect(x + 10, y + 25, 42, 90)
            if not bloqueia_movimento(pes, corpo, obstaculos):
                mudou = (x, y) != (self.x, self.y)
                self.x, self.y = x, y
                self.rect, self.bodyRect = pes, corpo
                if mudou:
                    self.ultima_movimentacao = pygame.time.get_ticks()

    def atacar(self):
        self.direcao_ataque = self.direcao
        self.inicio_ataque = pygame.time.get_ticks()
        self.inicio_interacao = -10000

        if self.direcao == "cima":
            ataque = pygame.Rect(self.bodyRect.centerx - 25, self.bodyRect.top - 35, 50, 45)

        elif self.direcao == "baixo":
            ataque = pygame.Rect(self.bodyRect.centerx - 25, self.bodyRect.bottom - 10, 50, 45)

        elif self.direcao == "direita":
            ataque = pygame.Rect(self.bodyRect.right - 10, self.bodyRect.centery - 25, 45, 50)

        else:
            ataque = pygame.Rect(self.bodyRect.left - 35, self.bodyRect.centery - 25, 45, 50)

        return ataque

    def recebeDano(self):
        if not self.viva:
            return
        self.vida = max(0, self.vida - 1)
        agora = pygame.time.get_ticks()
        self.inicio_dano = agora
        self.inicio_interacao = -10000
        if self.vida == 0:
            self.viva = False
            self.inicio_derrota = agora

    def draw(self, screen, camera):
        imagem, posicao = self.visual()
        screen.blit(imagem, camera.pos(*posicao))
