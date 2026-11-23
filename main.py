import os
from pathlib import Path
from functools import lru_cache

import pygame
from camera import Camera
from hud import HUD
from menu_principal import MenuPrincipal, MenuDerrota
from apresentacao_ilhas import ApresentacoesIlhas, DURACAO_DESCOBERTA_MS, FADE_SAIDA_MS, FADE_CARTELA_MS
from mapa_tesouro import TelaMapaTesouro
from dialogo_guardiao import DialogoGuardiao
from tela_continuacao import TelaContinuacao
from characters.kia import Kia
from scenes.ilha_afogada import IlhaAfogada
from scenes.ilha_dos_macacos import IlhaDosMacacos
from scenes.ilha_da_caveira import IlhaDaCaveira
from enemies.skeleton import Skeleton
from enemies.pirata import Pirata
from colisoes import bloqueia_movimento
from audio_jogo import AudioJogo

TELA_X, TELA_Y = 1280, 680
VIDA_KIA = 8
VIDA_SKELETON = 3
CURA_FRASCO = 3
BONUS_ARMADURA = 3
INTERVALO_DANO_AGUA_MS = 2000
PROTECAO_DANO_MS = 600
ESQUIVA_DURACAO_MS = 220
ESQUIVA_RECARGA_MS = 1100
# 220 px por esquiva: supera corpo de Kia (90) + inimigo (60),
# incluindo a distância de aproximação, sem terminar sobre o alvo.
ESQUIVA_VELOCIDADE = 1000


@lru_cache(maxsize=256)
def renderizar_texto(fonte, texto, cor):
    """Reutiliza textos estáticos sem manter uma referência ao jogo inteiro."""
    return fonte.render(texto, True, cor)


class Alpha:
    def __init__(self, screen):
        self.screen = screen
        self.hud = HUD()
        self.font = pygame.font.Font(None, 28)
        self.audio = AudioJogo()
        self.menu_principal = MenuPrincipal((TELA_X, TELA_Y))
        self.menu_derrota = MenuDerrota((TELA_X, TELA_Y))
        self.tela_continuacao = TelaContinuacao((TELA_X, TELA_Y))
        self.botao_continuacao_menu = self.tela_continuacao.botoes[0]
        self.apresentacoes = ApresentacoesIlhas((TELA_X, TELA_Y))
        self.tela_mapa = TelaMapaTesouro((TELA_X, TELA_Y))
        self.dialogo_guardiao = DialogoGuardiao((TELA_X, TELA_Y))
        for tela in (self.menu_principal,self.menu_derrota,self.tela_continuacao,
                     self.tela_mapa,self.dialogo_guardiao):
            tela.ao_som=self.som
        self.reiniciar()
        self.estado = 'inicio'
        self.audio.atualizar(self,pygame.time.get_ticks())

    def som(self, nome):
        self.audio.tocar(nome)


    def efeito(self, rect, cor, duracao=400):
        self.efeitos.append((rect.copy(), cor, pygame.time.get_ticks(), duracao))

    def reiniciar(self):
        self.ataques_executados_kia = 0
        self.derrota_em = None
        self.fala_chegada = None
        self.kia = Kia()
        self.vida_maxima = VIDA_KIA
        self.kia.vida = self.vida_maxima
        self.ultimo_dano = -PROTECAO_DANO_MS
        self.ultimo_dano_agua = -INTERVALO_DANO_AGUA_MS
        self.inicio_esquiva = -ESQUIVA_RECARGA_MS
        self.esquiva_ate = 0
        self.esquiva_atualizada = 0
        self.direcao_esquiva = pygame.Vector2()
        self.ilha_dos_macacos = IlhaDosMacacos()
        self.ilha = self.ilha_dos_macacos
        self.skeletons = []
        for px, py, cura in ((1920, 6510, False), (1240, 6010, False),
                             (1890, 5700, False), (1400, 4300, True),
                             (1740, 1900, False), (1120, 5670, False),
                             (1690, 5550, False)):
            self.skeletons.append(Skeleton(px-20, py-60, 'centro', cura,
                                           [(px-45, py-60), (px+5, py-60)]))
        self.piratas = []
        # O corpo do guarda do altar precisa nascer fora do frasco (1330, 3860).
        for px, py in ((1430, 3990), (1510, 1530)):
            self.piratas.append(Pirata(px-20, py-60, [(px-45, py-60), (px+5, py-60)]))
        self.piratas[0].indice_chave = 0
        self.piratas[1].indice_chave = 1
        self.guardas_labirinto = self.skeletons[:3]
        for inimigo in self.guardas_labirinto:
            inimigo.area_combate = self.ilha.limites_combate['ruinas']
        self.skeletons[3].area_combate = self.ilha.limites_combate['altar']
        self.skeletons[4].area_combate = self.ilha.limites_combate['cais']
        for inimigo in self.skeletons[5:]:
            inimigo.area_combate = pygame.Rect(1000, 5400, 800, 350)
        self.piratas[0].area_combate = self.ilha.limites_combate['altar']
        self.piratas[1].area_combate = self.ilha.limites_combate['cais']
        self.inimigos = self.skeletons + self.piratas
        rondas = (
            ((1380, 6530), (2020, 6530), (2020, 6650), (1380, 6650)),
            ((1100, 6000), (1380, 6000), (1380, 6230), (1100, 6230)),
            ((1690, 5620), (2080, 5620), (2080, 5800), (1850, 5800), (1850, 5620)),
            ((1250, 4320), (1720, 4320), (1720, 4120), (1250, 4120)),
            ((1510, 1810), (1770, 1810), (1770, 2120), (1510, 2120)),
            ((1150, 5480), (1200, 5480), (1200, 5680), (1080, 5680),
             (1080, 5550), (1150, 5550)),
            ((1620, 5480), (1750, 5480), (1750, 5700), (1620, 5700)),
            ((1220, 4050), (1760, 4050), (1760, 3730), (1220, 3730)),
            ((1390, 1490), (1820, 1490), (1820, 1640), (1390, 1640)),
        )
        for inimigo, ronda in zip(self.inimigos, rondas):
            inimigo.patrulha = ronda
            inimigo.ponto_pat = min(range(len(ronda)),
                                    key=lambda i: pygame.Vector2(ronda[i]).distance_squared_to(
                                        inimigo.rect.center))
        for skeleton in self.skeletons:
            skeleton.vida = VIDA_SKELETON
        for inimigo in self.inimigos:
            inimigo.vida_maxima = inimigo.vida
            inimigo.obter_obstaculos = self.obstaculos_movimento
            inimigo.em_terra = self.ilha.em_terra
            inimigo.ao_som = lambda nome,e=inimigo: self.audio.tocar_inimigo(nome,e,self.kia)
        self.cadaver_exam = False
        self.espada_on = False
        self.frascos = [r.copy() for r in self.ilha.frascos_exploracao]
        self.comentou_frasco = False
        self.frasco_ruins = False
        self.skeletons_derrotados = 0
        self.cadaveres_examinados = set()
        # 0 = altar; 1 = cais. Cada chave abre somente seu próprio baú.
        self.chaves = [None, None]
        self.chaves_dropadas = [False, False]
        self.tem_chave = [False, False]
        self.baus_abertos = [False, False]
        self.metade_mapa1 = False
        self.metade_mapa2 = False
        self.armadura = False
        self.ataque_r = None
        self.inicio_ataque = -1000
        self.atingidos = set()
        self.estado = 'exploracao'
        self.inicio_viagem = 0
        self.comentarios = set()
        self.aviso_mare_pendente = False
        self.efeitos = []
        self.tutorial_concluido = set()
        self.ilha_afogada = IlhaAfogada(pygame.time.get_ticks())
        self.ilha = self.ilha_afogada
        largura, altura = self.ilha.tamanho
        self.camera = Camera(TELA_X, TELA_Y, largura + TELA_X // 2, altura)
        self.posicionar_kia(*self.ilha.inicio)
        self.kia.direcao = 'cima'
        self.kia.image = self.kia.image_costas
        self.falar('Kia: Ahnn, que lugar é esse?', 6500)

    def posicionar_kia(self, x, y):
        self.kia.x, self.kia.y = x, y
        self.kia.rect.topleft = (x + 16, y + 100)
        self.kia.bodyRect.topleft = (x + 10, y + 25)
        self.camera.update(self.kia.bodyRect)

    def chegar_aos_macacos(self, agora):
        self.kia.reiniciar_animacoes()
        self.ilha = self.ilha_dos_macacos
        self.camera = Camera(TELA_X, TELA_Y, *self.ilha.tamanho)
        self.posicionar_kia(*self.ilha.inicio)
        self.kia.direcao = 'cima'
        self.kia.image = self.kia.image_costas
        self.esquiva_atualizada = self.esquiva_ate = agora
        self.fala_chegada = None
        self.iniciar_descoberta('macacos', agora)

    def chegar_a_caveira(self, agora):
        self.kia.reiniciar_animacoes()
        self.ilha = IlhaDaCaveira()
        self.camera = Camera(TELA_X, TELA_Y, *self.ilha.tamanho)
        self.inimigos = self.ilha.inimigos
        self.frascos = list(self.ilha.frascos)
        self.chaves = [None, None]
        self.chaves_dropadas = [False, False]
        self.tem_chave = [False, False]
        self.frasco_ruins = True
        self.ataque_r = None
        self.atingidos.clear()
        for inimigo in self.inimigos:
            self.ilha.configurar_inimigo(inimigo, self)
        self.posicionar_kia(*self.ilha.inicio)
        self.kia.direcao = 'cima'
        self.kia.image = self.kia.image_costas
        self.esquiva_atualizada = self.esquiva_ate = agora
        self.fala_chegada = 'Kia: Que lugar sombrio... Não há sinal de vida.'
        self.iniciar_descoberta('caveira', agora)

    def iniciar_descoberta(self, nome, agora):
        self.cena_saida = self.screen.copy()
        self.descoberta_id = nome
        self.inicio_descoberta = agora
        self.mensagem_ate = 0
        self.ataque_r = None
        self.estado = 'descoberta'

    def terminar_descoberta(self, agora):
        self.estado = 'chegada'
        self.inicio_chegada = agora

    def abrir_mapa_tesouro(self, agora):
        self.tela_mapa.iniciar(agora)
        self.ataque_r = None
        self.mensagem_ate = 0
        self.estado = 'mapa_tesouro'

    def abrir_dialogo_guardiao(self):
        self.dialogo_guardiao.iniciar(self.screen)
        self.ataque_r=None
        self.mensagem_ate=0
        self.estado='dialogo_guardiao'
        self.audio.atualizar(self,pygame.time.get_ticks())

    def renascer(self, agora):
        self.ataques_executados_kia = 0
        self.kia.reiniciar_animacoes()
        self.kia.vida = self.vida_maxima
        self.kia.viva = True
        self.derrota_em = None
        self.ataque_r = None
        self.atingidos.clear()
        self.efeitos.clear()
        self.mensagem_ate = 0
        self.esquiva_atualizada = self.esquiva_ate = agora
        self.inicio_esquiva = agora - ESQUIVA_RECARGA_MS
        self.ultimo_dano = agora + 900
        self.ultimo_dano_agua = agora
        if isinstance(self.ilha, IlhaAfogada) and self.ilha.inicio_mare is not None:
            # Dez segundos de maré baixa, sem revelar uma passagem ainda não descoberta.
            self.ilha.primeira_mare = False
            self.ilha.inicio_mare = agora + self.ilha.duracao_baixa
            self.ilha.atualizar_mare(agora)
            self.aviso_mare_pendente = False
        if isinstance(self.ilha, IlhaDaCaveira) and self.ilha.boss.vivo:
            ilha = self.ilha
            ilha.boss_ativo = False
            ilha.boss.vida = ilha.boss.vida_maxima
            ilha.boss.rect.topleft = (1280, 1540)
            ilha.boss_movendo = False
            ilha.acao = None
            ilha.invocacoes.clear()
            ilha.surgimentos.clear()
            ilha.recuperacao_ate = 0
            ilha.dano_boss_ate = 0
            ilha.reiniciar_dialogos_boss()
            ilha.ultimo_golpe = agora
            for inimigo in self.inimigos:
                if getattr(inimigo, 'invocado', False):
                    inimigo.vivo = False
            ilha.atualizar_obstaculos()
        for inimigo in self.inimigos:
            inimigo.caminho_desvio.clear()
            inimigo.last_atack = agora
            inimigo.reiniciar_animacoes()
        self.posicionar_kia(*self.ilha.inicio)
        self.kia.direcao = 'cima'
        self.kia.equipar_espada(self.espada_on)
        self.estado = 'exploracao'

    def falar(self, mensagem, duracao=None, legenda=False):
        self.autor_legenda = legenda if isinstance(legenda, str) else None
        aviso, separador, fala = mensagem.partition(' Kia:')
        self.aviso_coleta = aviso if separador else ''
        if separador:
            mensagem = 'Kia:' + fala
        self.mensagem = mensagem
        self.mensagem_narrativa = legenda or mensagem.startswith(('Kia:', 'A maré'))
        tempo_leitura = max(1800, min(4500, 1100 + len(mensagem)*32))
        duracao = tempo_leitura if duracao is None else min(duracao, tempo_leitura)
        self.mensagem_ate = pygame.time.get_ticks() + duracao

    def perto(self, rect, margem=40):
        return self.kia.bodyRect.colliderect(rect.inflate(margem, margem))

    def interacao(self):
        """O aviso e a ação de E usam o mesmo alvo."""
        if (self.estado != 'exploracao' or self.ilha is not self.ilha_dos_macacos
                or not self.kia.viva or self.esquivando()):
            return None
        for i, chave in enumerate(self.chaves):
            if chave is not None and self.perto(chave):
                return 'chave', i, '[E] Pegar chave'
        for i, frasco in enumerate(self.frascos):
            if self.perto(frasco):
                return 'frasco', i, self.aviso_frasco()
        if not self.frasco_ruins and self.perto(self.ilha.frasco_ruins):
            return 'frasco_ruins', None, self.aviso_frasco()
        if not self.cadaver_exam and self.perto(self.ilha.cadaver):
            return 'cadaver', None, '[E] Examinar'
        if self.cadaver_exam and not self.espada_on and self.perto(self.ilha.espada):
            return 'espada', None, '[E] Pegar espada'
        for i, (rect, _) in enumerate(self.ilha.cadaveres):
            if i not in self.cadaveres_examinados and self.perto(rect):
                return 'cadaver_pista', i, '[E] Examinar'
        for i, bau in enumerate((self.ilha.bau, self.ilha.bau_cais)):
            if self.perto(bau, 60):
                if self.bau_protegido(i):
                    aviso = 'Derrote os guardas do baú'
                elif not self.baus_abertos[i]:
                    aviso = '[E] Abrir baú' if self.tem_chave[i] else 'Baú trancado [E] Examinar'
                elif not (self.metade_mapa1 if i == 0 else self.armadura):
                    aviso = '[E] Pegar fragmento de mapa' if i == 0 else '[E] Pegar armadura'
                else:
                    aviso = 'Baú vazio'
                return 'bau', i, aviso
        if self.perto(self.ilha.barco, 80):
            pronto = self.metade_mapa1 and self.armadura
            return 'barco', None, '[E] Viajar para a Ilha das Caveiras' if pronto else '[E] Examinar barco'
        return None

    def bau_protegido(self, indice):
        return self.piratas[indice].vivo or self.skeletons[indice + 3].vivo

    def aviso_frasco(self):
        if self.kia.vida >= self.vida_maxima:
            return 'Vida cheia - o frasco permanece aqui'
        cura = min(CURA_FRASCO, self.vida_maxima - self.kia.vida)
        return f'[E] Pegar frasco (+{cura} de vida)'

    def obstaculos_movimento(self):
        obstaculos = list(self.ilha.obstaculos)
        if not isinstance(self.ilha, IlhaAfogada):
            obstaculos.extend(('frasco', r) for r in self.frascos)
            if not self.frasco_ruins:
                obstaculos.append(('frasco', self.ilha.frasco_ruins))
            obstaculos.extend(('chave', r) for r in self.chaves if r is not None)
        return obstaculos

    def obstaculos_kia(self):
        obstaculos = self.obstaculos_movimento()
        if not isinstance(self.ilha, IlhaAfogada):
            obstaculos.extend(('inimigo', e.rect) for e in self.inimigos if e.vivo)
        return obstaculos

    def posicionar_drop(self, rect, centro):
        """Evita que um item sólido apareça dentro dos pés de um personagem."""
        ocupados = [r for _, r in self.obstaculos_movimento()] + [self.kia.bodyRect, self.kia.rect]
        ocupados.extend(e.corpo_em(e.rect)
                        for e in self.inimigos if e.vivo)
        for distancia in range(0, 321, 32):
            for dx, dy in ((0, -1), (1, 0), (-1, 0), (0, 1),
                           (1, -1), (-1, -1), (1, 1), (-1, 1)):
                rect.center = (centro[0] + dx * distancia, centro[1] + dy * distancia)
                if (self.ilha.em_terra(rect)
                        and not any(rect.inflate(6, 6).colliderect(r) for r in ocupados)):
                    return
        rect.center = centro

    def objeto_interacao(self, tipo, indice):
        if tipo == 'chave':
            return self.chaves[indice]
        if tipo == 'frasco':
            return self.frascos[indice]
        if tipo == 'cadaver_pista':
            return self.ilha.cadaveres[indice][0]
        if tipo == 'bau':
            return (self.ilha.bau, self.ilha.bau_cais)[indice]
        return {'frasco_ruins': self.ilha.frasco_ruins,
                'cadaver': self.ilha.cadaver,
                'espada': self.ilha.espada,
                'barco': self.ilha.barco}[tipo]

    def interagir(self):
        if isinstance(self.ilha, IlhaDaCaveira):
            self.ilha.interagir(self)
            return
        alvo = self.interacao()
        if alvo is None:
            return
        tipo, i, _ = alvo
        if tipo in ('frasco', 'frasco_ruins') and self.kia.vida >= self.vida_maxima:
            return
        self.tutorial_concluido.add('interagir')
        if tipo != 'barco':
            self.kia.iniciar_interacao()
        if tipo == 'cadaver':
            self.cadaver_exam = True
            self.falar('Kia: Alguém esteve aqui antes de mim...')
        elif tipo == 'espada':
            self.espada_on = True
            self.kia.equipar_espada()
            self.som('coleta')
            self.efeito(self.ilha.espada, (245, 220, 135))
            self.falar('Espada adquirida', 4000)
        elif tipo == 'cadaver_pista':
            self.cadaveres_examinados.add(i)
            self.falar(self.ilha.cadaveres[i][1], 6500)
        elif tipo == 'chave':
            self.efeito(self.chaves[i], (245, 220, 135))
            self.som('coleta')
            self.tem_chave[i] = True
            self.chaves[i] = None
            self.falar('Chave adquirida.' if i == 0 else 'Chave adquirida.')
        elif tipo in ('frasco', 'frasco_ruins'):
            if self.kia.vida >= self.vida_maxima:
                return
            cura = min(CURA_FRASCO, self.vida_maxima - self.kia.vida)
            self.kia.vida += cura
            self.som('coleta')
            self.efeito(self.kia.rect, (125, 240, 150))
            falas = []
            if not self.comentou_frasco:
                falas.append('Sangue... Quem guardava esses frascos aqui?')
                self.comentou_frasco = True
            if tipo == 'frasco':
                self.frascos.pop(i)
            else:
                self.frasco_ruins = True
            mensagem = f'+{cura} de vida.'
            if falas:
                mensagem += ' Kia: ' + ' '.join(falas)
            self.falar(mensagem, 5000)
        elif tipo == 'bau':
            if self.bau_protegido(i):
                self.falar('Kia: Preciso derrotar os guardas para chegar a esse baú.')
                return
            if not self.baus_abertos[i]:
                if self.tem_chave[i]:
                    self.tem_chave[i] = False
                    self.baus_abertos[i] = True
                    self.som('bau')
                    self.efeito((self.ilha.bau, self.ilha.bau_cais)[i], (245, 220, 135))
                    self.falar('Um mapa! Está rasgado...' if i == 0
                               else 'Eu precisava mesmo dessa armadura.')
                else:
                    self.falar('Tá trancado. Onde está a chave?')
            elif i == 0 and not self.metade_mapa1:
                self.metade_mapa1 = True
                self.som('coleta')
                self.efeito(self.ilha.bau, (245, 220, 135))
                self.falar('Kia: Agora faz sentido! Estou presa em um arquipélago. Pera aí! '
                           'Tem um tesouro escondido em algum lugar entre as ilhas.', 11000)
            elif i == 1 and not self.armadura:
                self.armadura = True
                self.som('coleta')
                self.efeito(self.kia.rect, (170, 215, 240))
                self.vida_maxima += BONUS_ARMADURA
                self.kia.vida += BONUS_ARMADURA
                self.falar(' Eu precisava mesmo dessa armadura.', 6500)
        elif tipo == 'barco':
            if not self.metade_mapa1:
                self.falar('Kia: O barco ainda serve, mas preciso descobrir para onde seguir. Devo explorar o altar.')
            elif not self.armadura:
                self.falar('Kia: Talvez eu devesse olhar o que tem naquele baú.')
            else:
                self.estado = 'viagem'
                self.inicio_viagem = pygame.time.get_ticks()
                self.ataque_r = None

    def esquivando(self):
        return pygame.time.get_ticks() < self.esquiva_ate

    def atualizar_placa_afogada(self, now):
        ilha = self.ilha
        if ilha.leitura_placa_ate is not None:
            if now >= ilha.leitura_placa_ate:
                ilha.iniciar_mare(ilha.leitura_placa_ate)
                ilha.leitura_placa_ate = None
                self.aviso_mare_pendente = True
            return
        if (not ilha.placa_lida and not self.esquivando()
                and ilha.placa_proxima(self.kia.bodyRect)):
            ilha.placa_lida = True
            self.kia.iniciar_interacao()
            self.falar('Kia: O que será que isso significa?')
            ilha.leitura_placa_ate = self.mensagem_ate

    def esquivar(self):
        now = pygame.time.get_ticks()
        if (self.estado != 'exploracao' or not self.kia.viva
                or now - self.inicio_esquiva < ESQUIVA_RECARGA_MS):
            return
        keys = pygame.key.get_pressed()
        direcao = pygame.Vector2(int(keys[pygame.K_d]) - int(keys[pygame.K_a]),
                                 int(keys[pygame.K_s]) - int(keys[pygame.K_w]))
        if not direcao.length_squared():
            direcao = pygame.Vector2({'cima': (0, -1), 'baixo': (0, 1),
                                     'esquerda': (-1, 0), 'direita': (1, 0)}[self.kia.direcao])
        self.direcao_esquiva = direcao.normalize()
        self.inicio_esquiva = self.esquiva_atualizada = now
        self.esquiva_ate = now + ESQUIVA_DURACAO_MS
        self.esquiva_posicao_livre = (self.kia.x, self.kia.y)
        self.kia.iniciar_esquiva(self.direcao_esquiva, ESQUIVA_DURACAO_MS)
        self.ataque_r = None
        self.tutorial_concluido.add('esquivar')
        self.som('esquiva')
        self.som('kia_urro_esquiva')

    def mover_esquiva(self, now):
        if not hasattr(self, 'esquiva_posicao_livre'):
            self.esquiva_posicao_livre = (self.kia.x, self.kia.y)
        obstaculos = self.obstaculos_movimento()
        inimigos = [] if isinstance(self.ilha, IlhaAfogada) else [e for e in self.inimigos if e.vivo]
        ate = min(now, self.esquiva_ate)
        distancia = max(0, ate - self.esquiva_atualizada) * ESQUIVA_VELOCIDADE / 1000
        self.esquiva_atualizada = ate
        while distancia > 0:
            passo = min(2, distancia)
            x = self.kia.x + self.direcao_esquiva.x * passo
            y = self.kia.y + self.direcao_esquiva.y * passo
            pes = pygame.Rect(x + 16, y + 100, self.kia.rect.width, self.kia.rect.height)
            corpo = pygame.Rect(x + 10, y + 25, 42, 90)
            if (not self.ilha.em_terra(pes)
                    or bloqueia_movimento(pes, corpo, obstaculos)):
                self.esquiva_ate = now
                self.esquiva_atualizada = now
                self.kia.esquiva_ate = now
                break
            self.kia.x, self.kia.y = x, y
            self.kia.rect = pes
            self.kia.bodyRect.topleft = (x + 10, y + 25)
            if not any(corpo.colliderect(e.rect) for e in inimigos):
                self.esquiva_posicao_livre = (x,y)
            distancia -= passo
        if now >= self.esquiva_ate and any(self.kia.bodyRect.colliderect(e.rect) for e in inimigos):
            # A travessia é temporária: terminar dentro de alguém prenderia Kia.
            x0,y0 = self.esquiva_posicao_livre
            for recuo in range(0,193,2):
                x=x0-self.direcao_esquiva.x*recuo
                y=y0-self.direcao_esquiva.y*recuo
                pes=pygame.Rect(x+16,y+100,self.kia.rect.width,self.kia.rect.height)
                corpo=pygame.Rect(x+10,y+25,42,90)
                if (self.ilha.em_terra(pes) and not bloqueia_movimento(pes,corpo,obstaculos)
                        and not any(corpo.colliderect(e.rect) for e in inimigos)):
                    self.posicionar_kia(x,y)
                    break

    def evento(self, event):
        if event.type == pygame.QUIT:
            return False
        if self.estado == 'dialogo_guardiao':
            acao=self.dialogo_guardiao.evento(event)
            if acao=='concluir':
                self.ilha.conversou=True
                self.ilha.atualizar_obstaculos()
            if acao in ('concluir','fechar'):
                self.estado='exploracao'
            return True
        if self.estado == 'mapa_tesouro':
            if self.tela_mapa.evento(event) == 'continuar':
                self.estado = 'exploracao'
                self.falar('Kia: O mapa finalmente está completo! Já sei onde o tesouro está!')
            return True
        if self.estado == 'descoberta':
            agora=pygame.time.get_ticks()
            continuar=((event.type==pygame.KEYDOWN and event.key in (pygame.K_RETURN,pygame.K_KP_ENTER))
                       or (event.type==pygame.MOUSEBUTTONDOWN and event.button==1))
            if continuar and agora-self.inicio_descoberta>=1000:self.terminar_descoberta(agora)
            return not(event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE)
        if self.estado == 'derrota':
            acao = self.menu_derrota.evento(event)
            if acao == 'renascer':
                self.renascer(pygame.time.get_ticks())
            elif acao == 'menu':
                self.estado = 'inicio'
                self.menu_principal.selecionado = 0
            return True
        if self.estado == 'exploracao' and not self.kia.viva:
            return True
        if self.estado == 'continuacao':
            if self.tela_continuacao.evento(event) == 'menu':
                self.estado = 'inicio'
                self.menu_principal.selecionado = 0
            return True
        if self.estado == 'inicio':
            acao = self.menu_principal.evento(event)
            if acao == 'sair':return False
            if acao == 'jogar':self.reiniciar()
            return True
        if event.type != pygame.KEYDOWN:
            return True
        if event.key == pygame.K_ESCAPE:
            return False
        if self.estado == 'exploracao' and self.kia.viva:
            if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                self.esquivar()
            elif event.key == pygame.K_e:
                if isinstance(self.ilha, IlhaAfogada):
                    self.atualizar_placa_afogada(pygame.time.get_ticks())
                else:
                    self.interagir()
            elif event.key == pygame.K_SPACE and self.espada_on and not self.esquivando():
                now = pygame.time.get_ticks()
                if now - self.inicio_ataque >= 350:
                    self.ataque_r = self.kia.atacar()
                    self.inicio_ataque = now
                    self.atingidos.clear()
                    self.tutorial_concluido.add('atacar')
                    self.som('espada')
                    self.ataques_executados_kia += 1
                    self.som('kia_grito_ataque' if self.ataques_executados_kia % 2 == 0
                             else 'kia_urro_ataque')
        return True

    def atualizar(self):
        try:
            self.atualizar_logica()
        finally:
            self.audio.atualizar(self,pygame.time.get_ticks())

    def atualizar_logica(self):
        now = pygame.time.get_ticks()
        if self.estado == 'dialogo_guardiao':return
        if self.estado == 'mapa_tesouro':return
        if self.estado == 'descoberta':
            if now-self.inicio_descoberta>=DURACAO_DESCOBERTA_MS:self.terminar_descoberta(now)
            return
        if self.estado == 'partida_final':
            if now - self.inicio_partida_final >= 2400:
                self.estado = 'continuacao'
            return
        if self.estado == 'exploracao' and not self.kia.viva:
            self.ataque_r = None
            if self.derrota_em is None:
                self.derrota_em = now
            # A animação de queda termina antes de oferecer a escolha ao jogador.
            if now - self.derrota_em >= 1200:
                self.menu_derrota.selecionado = 0
                self.estado = 'derrota'
            return
        if self.estado == 'chegada':
            if now - self.inicio_chegada >= 450:
                self.estado = 'exploracao'
                if self.fala_chegada:
                    self.falar(self.fala_chegada)
                    self.fala_chegada = None
            return
        if self.estado == 'viagem':
            if now - self.inicio_viagem >= 3000:
                self.chegar_a_caveira(now)
            return
        if self.estado != 'exploracao' or not self.kia.viva:
            self.ataque_r = None
            return
        if isinstance(self.ilha, IlhaDaCaveira):
            self.ilha.atualizar(self, now)
            return
        inicio = isinstance(self.ilha, IlhaAfogada)
        if inicio:
            self.atualizar_placa_afogada(now)
            mare_subindo = self.ilha.subindo
            mare_alta = self.ilha.nivel_agua == 1 and not self.ilha.recuando
            self.ilha.atualizar_mare(now)
            if self.ilha.subindo and not mare_subindo:
                self.aviso_mare_pendente = True
            if self.aviso_mare_pendente and now >= self.mensagem_ate:
                self.falar('Kia: Ohh, não! A ilha está alagando', 7000)
                self.aviso_mare_pendente = False
            if self.ilha.nivel_agua == 1 and not self.ilha.recuando and not mare_alta:
                self.falar('Kia: Ah, droga! Como vou sair daqui?', 5000)
        anterior = self.kia.x, self.kia.y
        movimento_esquiva = self.esquiva_atualizada < self.esquiva_ate
        if movimento_esquiva:
            self.mover_esquiva(now)
        else:
            self.kia.move(self.obstaculos_kia(), *self.ilha.tamanho)
        if not self.ilha.em_terra(self.kia.rect):
            self.kia.x, self.kia.y = anterior
            self.kia.rect.topleft = (self.kia.x + 16, self.kia.y + 100)
            self.kia.bodyRect.topleft = (self.kia.x + 10, self.kia.y + 25)
        if (self.kia.x, self.kia.y) != anterior and not movimento_esquiva:
            self.tutorial_concluido.add('mover')
        self.camera.update(self.kia.bodyRect)
        if inicio:
            vista = pygame.Rect(self.camera.x, self.camera.y, TELA_X, TELA_Y)
            inicio_passagem = pygame.Rect(self.ilha.ponte[0], (240, 126))
            no_topo = self.ilha.no_morro(self.kia.rect)
            if (self.ilha.passagem_revelada and self.ilha.mare_baixa and no_topo
                    and vista.colliderect(inicio_passagem)
                    and 'passagem_avistada' not in self.comentarios):
                self.comentarios.add('passagem_avistada')
                self.falar('Kia: Uma ponte! Melhor atravessar antes que a maré volte a subir', 7000)
            if ('destrocos' not in self.comentarios
                    and now >= self.mensagem_ate
                    and self.kia.bodyRect.colliderect(self.ilha.area_destrocos)):
                self.comentarios.add('destrocos')
                self.falar('Kia: Será q mais alguém sobreviveu ao naufrágio?', 6500)
            if (self.ilha.na_agua(self.kia.rect)
                    and now - self.ultimo_dano_agua >= INTERVALO_DANO_AGUA_MS):
                self.kia.recebeDano()
                self.ultimo_dano_agua = now
                self.som('dano')
            if (self.ilha.passagem_revelada and self.ilha.mare_baixa
                    and self.ilha.saida.contains(self.kia.rect)):
                self.chegar_aos_macacos(now)
            return
        pirata = self.piratas[0]
        if (pirata.vivo and 'pirata_I' not in self.comentarios
                and now >= self.mensagem_ate
                and pygame.Vector2(pirata.rect.center).distance_to(self.kia.rect.center) <= 220):
            self.comentarios.add('pirata_I')
            self.falar('Kia: Ah, droga!')
        pirata_II = self.piratas[1]
        if (pirata_II.vivo and 'pirata_II' not in self.comentarios
                and self.camera.rect(pirata_II.rect).colliderect(pygame.Rect(0, 0, TELA_X, TELA_Y))):
            self.comentarios.add('pirata_II')
            self.falar('Kia: Mas que surpresa...')
        if self.ataque_r is not None:
            if now - self.inicio_ataque >= 180:
                self.ataque_r = None
            elif self.kia.ataque_ativo(now):
                for inimigo in self.inimigos:
                    if (inimigo.vivo and inimigo not in self.atingidos
                            and self.ataque_r.colliderect(inimigo.rect)):
                        inimigo.recebeDano()
                        if not inimigo.vivo:self.som('morte')
                        elif isinstance(inimigo,Pirata):self.som('inimigo_dano')
                        self.efeito(inimigo.rect, (235, 185, 120), 180 if inimigo.vivo else 500)
                        self.atingidos.add(inimigo)
                        if not inimigo.vivo:
                            if isinstance(inimigo, Skeleton) and not isinstance(inimigo, Pirata):
                                self.skeletons_derrotados += 1
                            if (inimigo.dropaFrasco
                                    or (isinstance(inimigo, Skeleton) and not isinstance(inimigo, Pirata)
                                        and self.skeletons_derrotados % 3 == 0)):
                                frasco = pygame.Rect(0, 0, 32, 46)
                                self.posicionar_drop(frasco, inimigo.rect.center)
                                self.frascos.append(frasco)
                            indice_chave = getattr(inimigo, 'indice_chave', None)
                            if indice_chave is not None and not self.chaves_dropadas[indice_chave]:
                                chave = pygame.Rect(0, 0, 40, 42)
                                self.posicionar_drop(chave, inimigo.rect.center)
                                self.chaves[indice_chave] = chave
                                self.chaves_dropadas[indice_chave] = True
                                if indice_chave == 0:
                                    self.falar('Kia: Isso abre o que?')
        ruinas_limpas = all(not inimigo.vivo for inimigo in self.guardas_labirinto)
        altar_limpo = not self.bau_protegido(0)
        if ruinas_limpas:
            self.ilha.liberar_etapa(1)
        if ruinas_limpas and altar_limpo and self.metade_mapa1:
            self.ilha.liberar_etapa(2)
        obstaculos_inimigos = self.obstaculos_movimento()
        for inimigo in self.inimigos:
            if not inimigo.vivo or not self.kia.viva:
                continue
            anterior = inimigo.rect.copy()
            # A praia inicial permite obter a espada antes da perseguição.
            patrulhando = (not self.espada_on
                          or not inimigo.area_combate.collidepoint(self.kia.rect.center)
                          or pygame.Vector2(inimigo.rect.center).distance_to(
                              self.kia.bodyRect.center) > inimigo.detected)
            if inimigo.caminho_desvio:
                inimigo.seguir_desvio(self.kia, self.inimigos)
            elif patrulhando:
                inimigo.patrulhar(self.kia, self.inimigos)
            else:
                inimigo.seguir(self.kia, self.inimigos)
            pes = pygame.Rect(inimigo.rect.x + 5, inimigo.rect.bottom - 12, 30, 12)
            corpo = pygame.Rect(inimigo.rect.centerx - 22, inimigo.rect.bottom - 100, 44, 100)
            if (not self.ilha.em_terra(pes)
                    or bloqueia_movimento(pes, corpo, obstaculos_inimigos)
                    ):
                inimigo.rect = anterior
            if inimigo.rect == anterior and not inimigo.caminho_desvio:
                if patrulhando:
                    for _ in range(len(inimigo.patrulha)):
                        px, py = inimigo.patrulha[inimigo.ponto_pat]
                        pes_alvo = pygame.Rect(px - 15, py + 18, 30, 12)
                        corpo_alvo = pygame.Rect(px - 22, py - 70, 44, 100)
                        if not bloqueia_movimento(pes_alvo, corpo_alvo, obstaculos_inimigos):
                            break
                        inimigo.ponto_pat = (inimigo.ponto_pat + 1) % len(inimigo.patrulha)
                alvo = (inimigo.patrulha[inimigo.ponto_pat] if patrulhando
                        else self.kia.bodyRect.center)
                if pygame.Vector2(inimigo.rect.center).distance_to(alvo) > 6:
                    inimigo.planejar_desvio(alvo)
            vida_anterior = self.kia.vida
            inimigo.atacar(self.kia, pode_atingir=(not self.esquivando()
                           and now - self.ultimo_dano >= PROTECAO_DANO_MS))
            if self.kia.vida < vida_anterior:
                self.ultimo_dano = now
                self.som('dano')
        if not self.kia.viva:
            self.ataque_r = None
            return
        if 'bote' not in self.comentarios and self.perto(self.ilha.barco, 80):
            self.comentarios.add('bote')
            self.falar('Kia: Vamos ver onde isso nos leva...')
        if now >= self.mensagem_ate:
            for nome, area, texto in self.ilha.comentarios:
                corpo = self.kia.bodyRect if nome == 'altar' else self.kia.rect
                if nome not in self.comentarios and corpo.colliderect(area):
                    self.comentarios.add(nome)
                    self.falar(texto)
                    break

    def dicas_tutorial(self):
        dicas = []
        if 'mover' not in self.tutorial_concluido:
            dicas.append('[WASD] mover')
        if self.espada_on:
            if 'atacar' not in self.tutorial_concluido:
                dicas.append('[SPACE] atacar')
            if 'esquivar' not in self.tutorial_concluido:
                dicas.append('[Shift + WASD] esquivar')
        return dicas

    def objetivo(self):
        if isinstance(self.ilha, IlhaDaCaveira):
            return self.ilha.objetivo(self)
        if isinstance(self.ilha, IlhaAfogada):
            if self.ilha.inicio_mare is None:
                return 'Investigue os cadáveres'
            if not self.ilha.passagem_revelada:
                return 'Abrigue-se no topo da ilha'
            return 'Investigue a nova passagem'
        if not self.cadaver_exam:
            return 'Explore a costa'
        if not self.espada_on:
            return 'Pegue a espada ao lado do cadáver'
        if (self.ilha.etapa_liberada == 0
                and self.ilha.limites_combate['ruinas'].collidepoint(self.kia.rect.center)
                and any(inimigo.vivo for inimigo in self.guardas_labirinto)):
            return 'Derrote os inimigos'
        if not self.metade_mapa1:
            if (self.ilha.limites_combate['altar'].collidepoint(self.kia.rect.center)
                    and self.bau_protegido(0)):
                return 'Derrote os inimigos'
            if self.baus_abertos[0]:
                return 'Pegue o fragmento de mapa'
            if self.tem_chave[0]:
                return 'Abra o baú próximo ao altar'
            if self.chaves[0] is not None:
                return 'Pegue a chave misteriosa'
            return 'Explore a floresta'
        if not self.armadura:
            if ('pirata_II' in self.comentarios
                    and self.bau_protegido(1)):
                return 'Derrote os inimigos'
            if self.baus_abertos[1]:
                return 'Pegue a armadura'
            if self.tem_chave[1]:
                return 'Abra o baú próximo ao cais'
            if self.chaves[1] is not None:
                return 'Pegue a chave do baú'
            if 'pirata_II' in self.comentarios:
                return 'Derrote os inimigos'
            return 'Explore a floresta'
        return 'Embarque no bote'

    def texto(self, texto, pos, cor=(255, 255, 255), fonte=None):
        fonte = fonte or self.font
        self.screen.blit(renderizar_texto(fonte, texto, (12, 20, 23)), (pos[0]+2, pos[1]+2))
        self.screen.blit(renderizar_texto(fonte, texto, cor), pos)

    def painel(self, rect, alpha=220):
        fundo = pygame.Surface(rect.size, pygame.SRCALPHA)
        fundo.fill((12, 24, 27, alpha))
        self.screen.blit(fundo, rect)

    def paragrafo(self, texto, x, y, largura):
        linhas = []
        linha = ''
        for palavra in texto.split():
            tentativa = (linha + ' ' + palavra).strip()
            if self.font.size(tentativa)[0] > largura and linha:
                linhas.append(linha)
                linha = palavra
            else:
                linha = tentativa
        linhas.append(linha)
        for i, linha in enumerate(linhas):
            pos = (x + (largura - self.font.size(linha)[0]) // 2, y + i * 27)
            contorno = self.font.render(linha, True, (0, 0, 0))
            for dx, dy in ((-1, -1), (0, -1), (1, -1), (-1, 0),
                           (1, 0), (-1, 1), (0, 1), (1, 1)):
                self.screen.blit(contorno, (pos[0] + dx, pos[1] + dy))
            self.texto(linha, pos)

    def painel_temporario(self, dicas, mensagem):
        # Blocos separados, ancorados acima da personagem e fora do HUD.
        linhas_mensagem = []
        linha = ''
        largura_texto = 620
        for palavra in mensagem.split():
            tentativa = (linha + ' ' + palavra).strip()
            if linha and self.font.size(tentativa)[0] > largura_texto:
                linhas_mensagem.append(linha)
                linha = palavra
            else:
                linha = tentativa
        if linha:
            linhas_mensagem.append(linha)
        blocos = [(dicas, (255, 255, 255)), (linhas_mensagem, (255, 255, 255))]
        blocos = [(linhas, cor) for linhas, cor in blocos if linhas]
        if not blocos:
            return
        altura = sum(20 + 28 * len(linhas) for linhas, _ in blocos) + 8 * (len(blocos) - 1)
        kia_tela = self.camera.rect(self.kia.bodyRect)
        y = max(12, kia_tela.top - altura - 43)
        for linhas, cor in blocos:
            largura = max(self.font.size(texto)[0] for texto in linhas) + 28
            rect = pygame.Rect(kia_tela.centerx - largura // 2, y, largura, 20 + 28 * len(linhas))
            rect.clamp_ip(pygame.Rect(12, 12, TELA_X - 24, TELA_Y - 24))
            for i, texto in enumerate(linhas):
                self.texto(texto, (rect.x + 14, rect.y + 10 + i * 28), cor)
            y = rect.bottom + 8


    def desenhar_hud(self, objetivo, mare=None, fala_boss_y=None):
        itens = []
        if self.espada_on:
            itens.append(('espada', 'Espada'))
        if self.armadura:
            itens.append(('armadura', 'Armadura'))
        if self.metade_mapa1:
            itens.append(('mapa', 'Mapa 2/2' if self.metade_mapa2 else 'Mapa 1/2'))
        chaves = sum(self.tem_chave)
        if chaves:
            itens.append(('chave', f'Chave ×{chaves}'))
        self.hud.desenhar(self.screen, self.kia.vida,
                          self.vida_maxima, itens, objetivo, mare)
        dicas = self.dicas_tutorial() if self.kia.viva and self.estado == 'exploracao' else []
        mensagem = self.mensagem if pygame.time.get_ticks() < self.mensagem_ate else ''
        if mensagem and self.mensagem_narrativa:
            dicas = []
        self.painel_temporario(dicas, self.aviso_coleta if mensagem and self.mensagem_narrativa else mensagem)
        if mensagem and self.mensagem_narrativa:
            if fala_boss_y is not None and mensagem.startswith('Rei Necromante:'):
                self.hud.dialogo(self.screen, mensagem, topo=fala_boss_y, exibir_autor=False)
            else:
                self.hud.dialogo(self.screen, mensagem, self.autor_legenda)

    def desenhar_aviso_interacao(self, objeto, aviso):
        self.hud.interacao(self.screen, self.camera.rect(objeto), aviso)

    def desenhar(self):
        if self.estado == 'dialogo_guardiao':
            self.dialogo_guardiao.desenhar(self.screen)
            return
        if self.estado == 'mapa_tesouro':
            self.tela_mapa.desenhar(self.screen)
            return
        if self.estado == 'descoberta':
            tempo=pygame.time.get_ticks()-self.inicio_descoberta
            if tempo<FADE_SAIDA_MS:
                self.screen.blit(self.cena_saida,(0,0))
                self.painel(self.screen.get_rect(),round(255*max(0,tempo)/FADE_SAIDA_MS))
            else:
                self.apresentacoes.desenhar(self.screen,self.descoberta_id)
                if tempo<FADE_SAIDA_MS+FADE_CARTELA_MS:
                    self.painel(self.screen.get_rect(),round(255*(1-(tempo-FADE_SAIDA_MS)/FADE_CARTELA_MS)))
                elif tempo>DURACAO_DESCOBERTA_MS-FADE_CARTELA_MS:
                    self.painel(self.screen.get_rect(),min(255,round(255*(tempo-DURACAO_DESCOBERTA_MS+FADE_CARTELA_MS)/FADE_CARTELA_MS)))
            return
        if self.estado == 'derrota':
            self.menu_derrota.desenhar(self.screen)
            return
        if self.estado == 'continuacao':
            self.desenhar_continuacao()
            return
        if self.estado == 'partida_final':
            self.ilha.desenhar(self)
            progresso = min(1, max(0, (pygame.time.get_ticks() - self.inicio_partida_final) / 2400))
            self.painel(self.screen.get_rect(), round(255 * progresso))
            return
        if self.estado == 'inicio':
            self.menu_principal.desenhar(self.screen)
            return
        if isinstance(self.ilha, IlhaDaCaveira):
            self.ilha.desenhar(self)
            self.desenhar_fade_chegada()
            return
        if isinstance(self.ilha, IlhaAfogada):
            self.ilha.desenhar_chao(self.screen, self.camera)
            imagem, posicao = self.kia.visual()
            self.ilha.desenhar_objetos(self.screen, self.camera,
                                       (imagem, posicao, self.kia.rect.bottom))
            agora = pygame.time.get_ticks()
            if self.kia.viva and self.ilha.na_agua(self.kia.rect):
                self.ilha.desenhar_respingos(self.screen, self.camera.rect(self.kia.rect), agora)
            mare = ('Maré subindo' if self.ilha.subindo else
                    'Maré recuando' if self.ilha.recuando else
                    'Maré baixa' if self.ilha.mare_baixa else 'Maré alta')
            segundos = self.ilha.segundos_restantes if self.ilha.inicio_mare is not None else None
            self.desenhar_hud(self.objetivo(), (mare, segundos))
            placa = self.ilha.placa_proxima(self.kia.bodyRect)
            if self.kia.viva and (placa or self.ilha.leitura_placa_ate is not None):
                rect, inscricao = placa or self.ilha.placas[0]
                self.hud.inscricao(self.screen, self.camera.rect(rect), inscricao)
            return
        imagem_kia, posicao_kia = self.kia.visual(self.ataque_r is not None)
        if pygame.time.get_ticks() - self.ultimo_dano < PROTECAO_DANO_MS:
            brilho = imagem_kia.copy()
            brilho.fill((210, 65, 65, 0), special_flags=pygame.BLEND_RGBA_ADD)
            brilho.set_alpha(130 if pygame.time.get_ticks() // 80 % 2 else 40)
            imagem_kia = imagem_kia.copy()
            imagem_kia.blit(brilho, (0, 0))
        personagens = [(self.kia.rect.bottom, imagem_kia, posicao_kia)]
        for inimigo in self.inimigos:
            if inimigo.vivo or inimigo.em_derrota():
                imagem, ancora = inimigo.visual()
                if imagem:
                    posicao = (inimigo.rect.centerx-ancora, inimigo.rect.bottom-imagem.get_height())
                    personagens.append((inimigo.rect.bottom, imagem, posicao))
        self.ilha.desenhar_fundo(self.screen, self.camera)
        self.ilha.desenhar_objetos(self.screen, self.camera, self.espada_on,
                                   self.baus_abertos[0], self.metade_mapa1,
                                   self.baus_abertos[1], self.armadura, personagens)
        frascos = list(self.frascos)
        if not self.frasco_ruins:
            frascos.append(self.ilha.frasco_ruins)
        for frasco in frascos:
            r = self.camera.rect(frasco)
            if self.ilha.sprite(self.screen, 'objects/frasco', r):
                continue
            pygame.draw.rect(self.screen, (170, 25, 45), r, border_radius=4)
            pygame.draw.rect(self.screen, (230, 215, 170), (r.x + 5, r.y - 3, 8, 5))
        for i, chave in enumerate(self.chaves):
            if chave is not None:
                r = self.camera.rect(chave)
                if self.ilha.sprite(self.screen, 'objects/chave', r):
                    continue
                cor = (255, 215, 65) if i == 0 else (155, 215, 240)
                pygame.draw.circle(self.screen, cor, (r.x + 6, r.centery), 6, 2)
                pygame.draw.line(self.screen, cor, (r.x + 12, r.centery), (r.right, r.centery), 3)
                pygame.draw.line(self.screen, cor, (r.right - 3, r.centery), (r.right - 3, r.bottom), 3)
        for inimigo in self.inimigos:
            if inimigo.vivo:
                r = self.camera.rect(inimigo.rect)
                max_vida = inimigo.vida_maxima
                if inimigo in self.piratas:
                    nome = 'Pirata Perdido ' + ('I' if inimigo is self.piratas[0] else 'II')
                    self.texto(nome, (r.centerx - self.font.size(nome)[0] // 2, r.y - 36))
                pygame.draw.rect(self.screen, (45, 25, 25), (r.x, r.y - 10, r.width, 5))
                pygame.draw.rect(self.screen, (185, 65, 55), (r.x, r.y - 10, r.width * inimigo.vida // max_vida, 5))
        if self.esquivando():
            pygame.draw.ellipse(self.screen, (170, 225, 235),
                                self.camera.rect(self.kia.rect.inflate(18, 8)), 2)
        if self.ataque_r is not None:
            r = self.camera.rect(self.ataque_r)
            fase = min(1, (pygame.time.get_ticks() - self.inicio_ataque) / 180)
            pygame.draw.arc(self.screen, (245, 224, 170), r.inflate(12, 12),
                            fase * 2, fase * 2 + 2.8, 4)
        now = pygame.time.get_ticks()
        self.efeitos = [e for e in self.efeitos if now - e[2] < e[3]]
        for rect, cor, inicio, duracao in self.efeitos:
            fase = (now - inicio) / duracao
            r = self.camera.rect(rect).inflate(int(fase * 30), int(fase * 30))
            pygame.draw.ellipse(self.screen, cor, r, max(1, int(4 * (1 - fase))))
        self.desenhar_hud(self.objetivo())
        alvo = self.interacao()
        if alvo:
            self.desenhar_aviso_interacao(self.objeto_interacao(alvo[0], alvo[1]), alvo[2])
        self.desenhar_fade_chegada()
        if self.estado == 'viagem':
            progresso = min(1, (pygame.time.get_ticks() - self.inicio_viagem) / 3000)
            self.painel(pygame.Rect(0, 0, TELA_X, TELA_Y), int(255 * progresso))

    def desenhar_fade_chegada(self):
        if self.estado == 'chegada':
            progresso=min(1,max(0,(pygame.time.get_ticks()-self.inicio_chegada)/450))
            self.painel(self.screen.get_rect(),round(255*(1-progresso)))

    def desenhar_continuacao(self):
        self.tela_continuacao.desenhar(self.screen)


def main():
    # Abrir pelo VS Code funciona mesmo com o terminal em outra pasta.
    os.chdir(Path(__file__).resolve().parent)
    # Cerca de 46 ms de áudio dão margem aos picos de processamento da fase.
    pygame.mixer.pre_init(44100,-16,2,2048)
    pygame.init()
    try:
        screen = pygame.display.set_mode((TELA_X, TELA_Y))
        pygame.display.set_caption('A Ilha Afogada - Alpha')
        jogo = Alpha(screen)
        clock = pygame.time.Clock()
        running = True
        while running:
            for event in pygame.event.get():
                if not jogo.evento(event):
                    running = False
            if not running:
                break
            jogo.atualizar()
            jogo.desenhar()
            pygame.display.flip()
            clock.tick(60)
    finally:
        pygame.quit()


if __name__ == '__main__':
    main()
