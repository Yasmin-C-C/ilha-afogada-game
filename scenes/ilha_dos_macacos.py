from functools import lru_cache
import logging
import random

import pygame

from asset_loader import ASSETS, carregar_imagem, carregar_sprite_recortado
from scenes.mar import desenhar_mar
from camera import Camera
from scenes.terreno import COR_AREIA, desenhar_pedras_pequenas, faixa_irregular
from scenes.planta import contorno_irregular


class IlhaDosMacacos:
    nome = 'Ilha dos Macacos'
    tamanho = (3200, 7800)
    inicio = (1572, 7460)
    tamanho_bloco = 512
    largura_trilha = 96
    trilhas = (
        ((1600, 7560), (1600, 7400), (1590, 6920), (1910, 6620), (1910, 6320), (1310, 6320),
         (1300, 5960), (1910, 5960), (1850, 5580), (1610, 5260)),
        ((1610, 5260), (1570, 4900), (1420, 4580), (1300, 4210), (1360, 3900),
         (1850, 3830), (1880, 3450), (1610, 3060), (1600, 2600)),
        ((1600, 2600), (1570, 2350), (1760, 2120), (1710, 1730),
         (1600, 1400), (1610, 1080)),
    )

    def __init__(self):
        self.sprites = {}
        self.sand = COR_AREIA
        self.path = (155, 124, 84)
        self.contornos_trilhas = [faixa_irregular(caminho, self.largura_trilha,
                                                 amplitude=8, semente=31 + i)
                                  for i, caminho in enumerate(self.trilhas)]
        self.costa = contorno_irregular((
            (1400, 7480), (1150, 7080), (1000, 6800), (750, 6550),
            (700, 5850), (860, 5580), (1300, 5300), (1320, 5050),
            (1380, 4850), (1150, 4550), (900, 4300), (850, 3600),
            (1100, 3320), (1440, 3030), (1450, 2700), (1370, 2490),
            (1170, 2280), (1080, 1800), (1230, 1400), (1470, 1180),
            (1490, 1050), (1720, 1050), (1730, 1180), (1940, 1450),
            (2110, 1800), (2040, 2270), (1820, 2490), (1740, 2700),
            (1760, 3030), (2110, 3320), (2260, 3600), (2230, 4300),
            (1920, 4550), (1780, 4850), (1800, 5050), (1850, 5300),
            (2200, 5580), (2320, 5850), (2270, 6550), (2010, 6800),
            (1850, 7080), (1760, 7480)), 22)
        fim_travessia = self.tamanho[1] + 680
        self.eixo_travessia = ((1603, fim_travessia), (1603, 7250))
        self.contorno_travessia = faixa_irregular(self.eixo_travessia, 126, passo=32)
        self.cadaver = pygame.Rect(1380, 7190, 120, 72)
        self.espada = pygame.Rect(1540, 7220, 55, 22)
        self.cadaverS = carregar_imagem('objects/cadaver.png', self.cadaver.size)
        self.espadaS = carregar_imagem('objects/espada.png', self.espada.size)
        self.bau = pygame.Rect(1561, 3612, 78, 68)
        self.bau_cais = pygame.Rect(1830, 1670, 78, 68)
        self.frasco_ruins = pygame.Rect(1120, 6280, 32, 46)
        self.frascos_exploracao = [pygame.Rect(1330, 3860, 32, 46)]
        self.visual_altar = pygame.Rect(1450, 3300, 300, 300)
        self.altar = pygame.Rect(1466, 3525, 268, 75)
        self.areas_combate = {
            'ruinas': contorno_irregular(((850, 5670), (1600, 5500), (2180, 5700),
                                         (2180, 6580), (1600, 6750), (850, 6570)), 15),
            'altar': contorno_irregular(((1060, 3430), (1540, 3240), (2080, 3450),
                                        (2120, 4270), (1650, 4460), (1070, 4250)), 15),
            'cais': contorno_irregular(((1230, 1470), (1600, 1280), (1930, 1470),
                                       (2000, 2180), (1600, 2390), (1210, 2190)), 15),
        }
        self.limites_combate = {}
        for nome, pontos in self.areas_combate.items():
            limite = pygame.Rect(pontos[0], (1, 1))
            for ponto in pontos[1:]:
                limite.union_ip(pygame.Rect(ponto, (1, 1)))
            self.limites_combate[nome] = limite.inflate(100, 100)
        self.portoes = [pygame.Rect(1230, 5080, 700, 34), pygame.Rect(1330, 2710, 540, 34)]
        # As passagens do labirinto ao altar e do altar ao cais ficam abertas.
        self.etapa_liberada = 2
        self.muros = [
            pygame.Rect(980, 6400, 780, 70),
            pygame.Rect(1460, 6090, 690, 70),
            pygame.Rect(980, 5780, 780, 70),
            pygame.Rect(920, 5770, 65, 620),
            pygame.Rect(2150, 6090, 65, 520),
            pygame.Rect(1070, 3460, 65, 330),
            pygame.Rect(1070, 4000, 65, 260),
            pygame.Rect(2050, 3480, 65, 320),
            pygame.Rect(2050, 4010, 65, 250),
        ]
        self.contorno_cais = ((1490, 1120), (1490, 600), (1730, 600), (1730, 1120))
        self.cais = pygame.Rect(1490, 600, 240, 520)
        self.pilares_cais=[pygame.Rect(x-14,y-48,28,60)
                          for x in (self.cais.left+12,self.cais.right-12)
                          for y in (self.cais.top+30,self.cais.top+250,self.cais.bottom-20)]
        self.barco = pygame.Rect(1225, 620, 245, 365)
        self.cadaveres = [(pygame.Rect(2005, 6194, 110, 102),
                          'Kia: Ele não conseguiu sair destas ruínas...'),
                         (pygame.Rect(1246, 1785, 110, 102),
                          'Kia: Alguém tentou escapar por este cais...')]
        self.cadaver_pistaS = carregar_imagem('objects/cadaver-cemiterio.png', (110, 102))
        self.decoracoes = [
            ('fite', pygame.Rect(1280, 7045, 62, 62)),
            ('barril', pygame.Rect(1219, 6994, 46, 60)),
            ('caixa', pygame.Rect(1268, 6952, 56, 52)),
            ('estatua', pygame.Rect(1450, 6924, 64, 128)),
            ('estatua', pygame.Rect(1670, 6924, 64, 128)),
            ('caixa', pygame.Rect(1127, 6469, 56, 52)),
            ('barril', pygame.Rect(1061, 6463, 46, 60)),
            ('barril_deitado', pygame.Rect(1184, 6488, 64, 48)),
            ('caixa', pygame.Rect(1400, 5840, 64, 48)),
            ('barril', pygame.Rect(1284, 5834, 46, 60)),
            ('barril_deitado', pygame.Rect(1335, 5860, 60, 44)),
            ('ruina-pedra', pygame.Rect(1070, 5768, 136, 136)),
            ('ruina-pedra', pygame.Rect(1600, 6080, 136, 136)),
            ('caixa', pygame.Rect(990, 6260, 56, 56)),
            ('caixa', pygame.Rect(990, 6320, 56, 56)),
            ('caixa', pygame.Rect(1054, 6320, 56, 56)),
            ('estatua', pygame.Rect(1070, 3800, 64, 154)),
            ('estatua', pygame.Rect(2050, 3810, 64, 154)),
            ('barril', pygame.Rect(1280, 2040, 50, 65)),
            ('caixa', pygame.Rect(1276, 2109, 50, 48)),
            ('barril_deitado', pygame.Rect(1830, 1920, 68, 50)),
            ('fite', pygame.Rect(1883, 1967, 62, 62)),
        ]
        for x, y in ((1290, 5595), (1420, 5595), (1540, 5595),
                     (1295, 5705), (1440, 5705), (1570, 5705)):
            tumulo = pygame.Rect(0, 0, 64, 82)
            tumulo.midbottom = (x, y)
            self.decoracoes.append(('tumulo', tumulo))
        self.baus_quebrados = [pygame.Rect(1270, 1700, 95, 80),
                              pygame.Rect(1280, 2340, 100, 84)]
        self.arvores = []
        self.bananeiras_sem_macacos = []
        for n, (x, y) in enumerate((
            (1170, 6930), (1190, 6672), (840, 6280), (2210, 5900),
            (1250, 5390), (1910, 5430), (1420, 4820), (1770, 4800),
            (1230, 4530), (2050, 4380), (970, 3920), (2200, 3660),
            (1200, 3340), (1930, 3300), (1470, 2633), (1680, 2960),
            (1310, 2380), (1860, 2350), (1170, 1840), (2050, 1810),
            (970, 6585), (1065, 6685), (1385, 6805), (1535, 6830),
            (1331, 6872),
        )):
            r = pygame.Rect(0, 0, 180+n%3*12, 240+n%3*12)
            r.midbottom = (x, y)
            self.arvores.append(r)
            if n % 2 == 0:
                self.bananeiras_sem_macacos.append(r)
        self.pedras_barreira = [pygame.Rect(x, y, 65+n%3*10, 50+n%3*8)
                               for n,(x,y) in enumerate(((1020,6860),(1950,6820),
                                 (770,6010),(2240,6330),(1270,5240),(1810,5220),
                                 (930,3680),(2160,4130),(1380,2870),(1760,2850),
                                 (1160,2100),(1940,1570)))]
        self.pedras_barreira.extend((pygame.Rect(2018, 1898, 62, 48),
                                     pygame.Rect(2020, 1962, 45, 40),
                                     pygame.Rect(1850, 2352, 64, 46),
                                     pygame.Rect(1820, 2325, 30, 27)))
        self.pedras_areia = [pygame.Rect(x,y,18+n%3*6,14+n%2*5)
                            for n,(x,y) in enumerate(((1500,7320),(1700,7310),(1380,6910),
                               (1860,6880),(1220,6180),(1810,6330),(2020,5960),(1100,5640),
                               (1460,4930),(1680,4750),(1290,4350),(1840,4090),
                               (1240,3740),(1960,3440),(1550,3110),(1580,2510),
                               (1430,2200),(1840,1740)))]
        self.arbustos = []
        self.fala_altar = 'Que tipo de Deus sinistro é esse?'
        self.comentarios = [
            ('ruinas', self.limites_combate['ruinas'], 'Kia: Isso é... Um esqueleto vivo?'),
            ('pos_labirinto', pygame.Rect(1280, 4540, 620, 480),
             'Kia: Eu estou louca ou acabei de lutar com esqueletos vivos?'),
            ('altar', self.bau.inflate(160, 160), 'Kia: ' + self.fala_altar),
            ('cais', self.limites_combate['cais'], 'Kia: Um cais abandonado... Talvez o bote ainda sirva.'),
        ]
        terra = pygame.Surface(self.tamanho, pygame.SRCALPHA)
        for pontos in (self.costa, self.contorno_travessia, self.contorno_cais):
            pygame.draw.polygon(terra, 'white', pontos)
        self.terra = pygame.mask.from_surface(terra)
        self.construir_obstaculos()
        self.afastar_pedras_das_trilhas()
        self.construir_obstaculos()
        self.distribuir_pedras()
        self.camadas_fixas = []
        self.imagem_cais=pygame.Surface(self.cais.size,pygame.SRCALPHA)
        self.imagem_cais.fill((76,54,35))
        tabuas=carregar_sprite_recortado('objects/cais-tabuas.png',(self.cais.width,80))
        for y in range(-4,self.cais.height,76):
            self.imagem_cais.blit(tabuas,(0,y))
        for r in self.pilares_cais:
            self.camadas_fixas.append((r.bottom,
                carregar_sprite_recortado('objects/cais-pilar.png',r.size),r.topleft))
        for nome,r in self.decoracoes:
            deitado = nome.endswith('_deitado')
            arquivo = nome.removesuffix('_deitado')
            caminho = 'objects/bau-quebrado.webp' if arquivo == 'bau_quebrado' else 'objects/'+arquivo+'.png'
            imagem = carregar_imagem(caminho,r.size,90 if deitado else 0)
            self.camadas_fixas.append((r.bottom,imagem,r.topleft))
        for r in self.arvores:
            arquivo = 'bananeira-sem-macacos' if r in self.bananeiras_sem_macacos else 'trees'
            self.camadas_fixas.append((r.bottom,carregar_imagem('objects/'+arquivo+'.png',r.size),r.topleft))
        for arquivo,retangulos in (('pedra',self.pedras_barreira),
                                   ('bau-quebrado.webp',self.baus_quebrados)):
            caminho = 'objects/'+arquivo if '.' in arquivo else 'objects/'+arquivo+'.png'
            for r in retangulos:
                self.camadas_fixas.append((r.bottom,carregar_imagem(caminho,r.size),r.topleft))
        for r in self.muros:
            self.camadas_fixas.append((r.bottom,self.imagem_muro(r.size),(r.x,r.y-24)))
        self.camadas_fixas.extend([
            (self.altar.bottom,carregar_imagem('objects/altar.webp',self.visual_altar.size),self.visual_altar.topleft),
            (self.barco.bottom,carregar_imagem('objects/bote.png',self.barco.size,95),self.barco.topleft),
            (self.cadaver.bottom,self.cadaverS,self.cadaver.topleft),
        ])
        for r,_ in self.cadaveres:
            self.camadas_fixas.append((r.bottom,self.cadaver_pistaS,r.topleft))
        self.imagens_baus = {}

    def na_trilha(self, rect):
        margem = self.largura_trilha + 40
        limite = rect.inflate(margem, margem)
        return any(limite.clipline(a, b) for caminho in self.trilhas
                   for a, b in zip(caminho, caminho[1:]))

    def afastar_pedras_das_trilhas(self):
        protegidos = [r.inflate(16, 16) for nome, r in self.obstaculos if nome != 'pedra']
        for pedra in self.pedras_barreira + self.pedras_areia:
            if not self.na_trilha(pedra):
                continue
            origem = pedra.copy()
            for distancia in range(40, 641, 40):
                candidatos = [origem.move(dx * distancia, dy * distancia)
                              for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1),
                                             (-1, -1), (1, -1), (-1, 1), (1, 1))]
                destino = next((r for r in candidatos if self.em_terra(r.inflate(8, 8))
                                and not self.na_trilha(r)
                                and not any(r.colliderect(p) for p in protegidos)
                                and not any(r.colliderect(p.inflate(8, 8))
                                            for p in self.pedras_barreira + self.pedras_areia
                                            if p is not pedra)), None)
                if destino is not None:
                    pedra.topleft = destino.topleft
                    break

    def distribuir_pedras(self):
        """Pedras pequenas decoram cada trecho sem criar novas barreiras."""
        aleatorio = random.Random(210859)
        protegidos = [r.inflate(32, 32) for _, r in self.obstaculos]
        # Mantém livre o ponto onde o conjunto de pedras foi retirado.
        protegidos.append(pygame.Rect(1720, 2395, 85, 75))
        protegidos.extend(r.inflate(32, 32) for r in
                          [self.espada, self.frasco_ruins, *self.frascos_exploracao])
        for faixa in range(1400, 7400, 400):
            for agrupadas in (False, True):
                for tentativa in range(80):
                    x = aleatorio.randint(1000, 2150)
                    y = faixa + aleatorio.randint(0, 260)
                    pedras = []
                    for dx, dy in (((0, 0), (29, -10), (39, 20)) if agrupadas else ((0, 0),)):
                        largura = aleatorio.randint(16, 29)
                        pedras.append(pygame.Rect(x + dx, y + dy, largura, round(largura * .75)))
                    if all(self.em_terra(r.inflate(12, 12))
                           and not self.na_trilha(r)
                           and not any(r.colliderect(p) for p in protegidos)
                           for r in pedras):
                        self.pedras_areia.extend(pedras)
                        protegidos.extend(r.inflate(18, 18) for r in pedras)
                        break

    @lru_cache(maxsize=16)
    def imagem_muro(self, tamanho):
        largura, altura = tamanho
        imagem = pygame.Surface((largura, altura + 24), pygame.SRCALPHA)
        aleatorio = random.Random(largura * 17 + altura)
        pygame.draw.rect(imagem, (61, 62, 52), (0, 24, largura, altura))
        pygame.draw.rect(imagem, (80, 79, 66), (0, 5, largura, altura))
        for y in range(0, altura, 24):
            inicio = -28 if y // 24 % 2 else 0
            for x in range(inicio, largura, 56):
                desvio = aleatorio.randint(-9, 9)
                topo = y + (aleatorio.randint(0, 7) if y == 0 else 2)
                bloco = pygame.Rect(x + 2, topo, 52, min(21, altura - topo))
                pygame.draw.rect(imagem, (126 + desvio, 124 + desvio, 100 + desvio), bloco)
                pygame.draw.line(imagem, (165, 159, 128), bloco.topleft, bloco.topright, 2)
                pygame.draw.line(imagem, (94, 94, 76), bloco.bottomleft, bloco.bottomright, 2)
                if aleatorio.random() < .38:
                    cx = max(2, min(largura - 3, x + 27))
                    pygame.draw.lines(imagem, (81, 82, 67), False,
                                      ((cx, topo + 2), (cx - 4, topo + 8),
                                       (cx + 1, min(topo + 17, altura))), 2)
        return imagem

    def liberar_etapa(self, etapa):
        if etapa>self.etapa_liberada:
            self.etapa_liberada=etapa
            self.construir_obstaculos()

    def construir_obstaculos(self):
        self.obstaculos=[('altar',self.altar)]
        self.obstaculos.extend(('pilar',pygame.Rect(r.centerx-8,r.bottom-14,16,14))
                               for r in self.pilares_cais)
        self.obstaculos.extend(('muro',r) for r in self.muros)
        self.obstaculos.extend(('portao',r) for n,r in enumerate(self.portoes) if n>=self.etapa_liberada)
        self.obstaculos.extend(('pedra',r.inflate(-8,-8)) for r in self.pedras_barreira)
        self.obstaculos.extend(('arvore',pygame.Rect(r.centerx-12,r.bottom-20,24,20)) for r in self.arvores)
        self.obstaculos.extend(('bau',r) for r in (self.bau,self.bau_cais))
        self.obstaculos.extend((nome,pygame.Rect(r.x+4,r.bottom-24,r.width-8,24))
                               for nome,r in self.decoracoes)
        self.obstaculos.append(('cadaver',self.cadaver.inflate(-24,-24)))
        self.obstaculos.extend(('cadaver',r.inflate(-24,-24)) for r,_ in self.cadaveres)
        self.obstaculos.append(('barco',self.barco.inflate(-36,-20)))
        self.obstaculos.extend(('bau quebrado',pygame.Rect(r.x+10,r.bottom-26,r.width-20,26))
                               for r in self.baus_quebrados)


    def sprite(self, screen, nome, rect):
        chave = (nome, rect.size)
        if chave not in self.sprites:
            aliases = {'objects/bau_fechado': 'objects/bau',
                       'objects/mapa_metade': 'objects/mapa1',
                       'objects/barco': 'objects/bote'}
            caminho = ASSETS / (nome + '.png')
            if not caminho.is_file():
                caminho = ASSETS / (aliases.get(nome, nome) + '.png')
            imagem = None
            if caminho.is_file():
                try:
                    original = carregar_imagem(caminho.relative_to(ASSETS).as_posix())
                    if nome=='objects/bau_aberto':
                        original=original.subsurface(original.get_bounding_rect(min_alpha=8))
                    proporcao = min(rect.width / original.get_width(), rect.height / original.get_height())
                    tamanho = (max(1, round(original.get_width() * proporcao)),
                               max(1, round(original.get_height() * proporcao)))
                    imagem = pygame.Surface(rect.size, pygame.SRCALPHA)
                    reduzida = pygame.transform.scale(original, tamanho)
                    imagem.blit(reduzida, ((rect.width - tamanho[0]) // 2, rect.height - tamanho[1]))
                except pygame.error as erro:
                    logging.warning('Sprite inválido %s: %s', caminho, erro)
            self.sprites[chave] = imagem
        imagem = self.sprites[chave]
        if imagem is None:
            return False
        screen.blit(imagem, rect)
        return True

    def desenhar_bau(self, screen, rect, aberto, coletado, conteudo):
        nome = 'objects/bau_aberto' if aberto else 'objects/bau_fechado'
        visual=pygame.Rect(rect.x,rect.y-16,rect.width,rect.height+16) if aberto else rect
        if not self.sprite(screen, nome, visual):
            pygame.draw.rect(screen, (115, 65, 25), rect)
            pygame.draw.rect(screen, (220, 175, 65), rect, 3)
            if aberto:
                pygame.draw.rect(screen, (45, 30, 20), rect.inflate(-10, -10))
                pygame.draw.rect(screen, (170, 110, 45), (rect.x, rect.y - 12, rect.width, 12))
            else:
                pygame.draw.rect(screen, (240, 200, 65), (rect.centerx - 5, rect.centery - 6, 10, 12))
        if aberto and not coletado:
            tamanho = (46, 44) if conteudo == 'mapa_metade' else (30, 20)
            item = pygame.Rect(0, 0, *tamanho)
            item.center = rect.center
            if not self.sprite(screen, 'objects/' + conteudo, item):
                cor = (245, 225, 165) if conteudo == 'mapa_metade' else (175, 200, 210)
                pygame.draw.rect(screen, cor, item)

    def em_terra(self, rect):
        largura, altura = self.terra.get_size()
        return all(0 <= x < largura and 0 <= y < altura and self.terra.get_at((x, y))
                   for x, y in ((rect.left, rect.top), (rect.right - 1, rect.top),
                                (rect.left, rect.bottom - 1), (rect.right - 1, rect.bottom - 1)))

    def draw(self, screen, espada_on, camera, bau_altar_aberto=False, metade_mapa1=False,
             cadaver_exam=False, bau_cais_aberto=False, armadura=False, nivel_travessia=0,
             personagens=()):
        self.desenhar_fundo(screen, camera, nivel_travessia)
        self.desenhar_objetos(screen, camera, espada_on, bau_altar_aberto, metade_mapa1,
                              bau_cais_aberto, armadura, personagens)

    def desenhar_fundo(self, screen, camera, nivel_travessia=0):
        desenhar_mar(screen, camera)
        if nivel_travessia < 1:
            contorno = (self.contorno_travessia if nivel_travessia == 0 else
                        faixa_irregular(self.eixo_travessia, 126 * (1 - nivel_travessia),
                                         amplitude=8 * (1 - nivel_travessia), passo=32))
            pontos = [camera.pos(*p) for p in contorno]
            pygame.draw.polygon(screen, COR_AREIA, pontos)
        lado=self.tamanho_bloco
        x0=max(0,camera.x//lado)
        y0=max(0,camera.y//lado)
        for linha in range(y0,min((self.tamanho[1]-1)//lado,(camera.y+screen.get_height())//lado)+1):
            for coluna in range(x0,min((self.tamanho[0]-1)//lado,(camera.x+screen.get_width())//lado)+1):
                screen.blit(self.bloco_cenario(coluna,linha),camera.pos(coluna*lado,linha*lado))

    @lru_cache(maxsize=32)
    def bloco_cenario(self,coluna,linha):
        lado=self.tamanho_bloco
        imagem=pygame.Surface((lado,lado),pygame.SRCALPHA).convert_alpha()
        camera=Camera(lado,lado,*self.tamanho)
        camera.x,camera.y=coluna*lado,linha*lado
        self.desenhar_cenario(imagem,camera)
        return imagem

    def desenhar_objetos(self, screen, camera, espada_on=False, bau_altar_aberto=False,
                          metade_mapa1=False, bau_cais_aberto=False, armadura=False,
                          personagens=()):
        camadas = self.camadas_fixas + list(personagens)
        for r, aberto, coletado, conteudo in (
            (self.bau, bau_altar_aberto, metade_mapa1, 'mapa_metade'),
            (self.bau_cais, bau_cais_aberto, armadura, 'armadura')):
            chave = (aberto, coletado, conteudo)
            if chave not in self.imagens_baus:
                imagem = pygame.Surface((r.width, r.height+16), pygame.SRCALPHA)
                self.desenhar_bau(imagem, pygame.Rect(0, 16, *r.size), aberto, coletado, conteudo)
                self.imagens_baus[chave] = imagem
            camadas.append((r.bottom, self.imagens_baus[chave], (r.x, r.y-16)))
        for n,r in enumerate(self.portoes):
            if n>=self.etapa_liberada:
                camadas.append((r.bottom,self.imagem_muro(r.size),(r.x,r.y-24)))
        if not espada_on:
            camadas.append((self.espada.bottom, self.espadaS, self.espada.topleft))
        for _, imagem, posicao in sorted(camadas, key=lambda camada: camada[0]):
            destino = camera.rect(imagem.get_rect(topleft=posicao))
            if screen.get_rect().colliderect(destino):
                screen.blit(imagem, destino)

    def desenhar_cenario(self,screen,camera):
        costa=[camera.pos(*p) for p in self.costa]
        pygame.draw.polygon(screen,self.sand,costa)
        centro=pygame.Vector2(1600,4000)
        interior=[camera.pos(*pygame.Vector2(p).lerp(centro,.022)) for p in self.costa]
        solo=pygame.Surface(screen.get_size(),pygame.SRCALPHA)
        solo.fill((57,94,49,255))
        for nome,area in self.areas_combate.items():
            cor={'ruinas':(108,111,81),'altar':(103,109,72),'cais':(118,104,74)}[nome]
            pygame.draw.polygon(solo,cor,[camera.pos(*p) for p in area])
        for contorno in self.contornos_trilhas:
            pygame.draw.polygon(solo,self.path,[camera.pos(*p) for p in contorno])
        limite=pygame.Surface(screen.get_size(),pygame.SRCALPHA)
        pygame.draw.polygon(limite,'white',interior)
        solo.blit(limite,(0,0),special_flags=pygame.BLEND_RGBA_MIN)
        screen.blit(solo,(0,0))
        desenhar_pedras_pequenas(screen,camera,self.pedras_areia)
        screen.blit(self.imagem_cais,camera.pos(self.cais.x,self.cais.y))
