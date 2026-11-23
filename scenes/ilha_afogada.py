import random

import pygame

from asset_loader import carregar_imagem, carregar_sprite_recortado
from camera import Camera
from scenes.mar import desenhar_mar
from scenes.terreno import COR_AREIA, desenhar_pedras_pequenas, faixa_irregular


def ponto_no_poligono(ponto, vertices):
    x, y = ponto
    dentro = False
    for (ax, ay), (bx, by) in zip(vertices, vertices[1:] + vertices[:1]):
        if (ay > y) != (by > y) and x < ax + (bx - ax) * (y - ay) / (by - ay):
            dentro = not dentro
    return dentro


def planta(x, y):
    return (120 + round((x - 110) * 2), 140 + round((y - 657) * 2))


class IlhaAfogada:
    nome = 'Ilha Afogada'
    tamanho = (1700, 1430)
    inicio = (627, 1060)
    duracao_baixa = 10000
    duracao_subida = 7000
    duracao_primeira_subida = 12000
    duracao_alta = 3000
    duracao_recuo = 7000

    def __init__(self, agora):
        self.inicio_mare = None
        self.primeira_mare = True
        self.placa_lida = False
        self.leitura_placa_ate = None
        self.passagem_revelada = False
        self.costa = tuple(planta(*p) for p in (
            (110, 913), (153, 760), (247, 689), (385, 657),
            (528, 695), (584, 791), (632, 851), (667, 928),
            (594, 1130), (527, 1152), (383, 1198), (248, 1143), (144, 1068)))
        area_central = tuple(planta(*p) for p in (
            (220, 867), (300, 803), (445, 803), (551, 865),
            (552, 943), (448, 991), (310, 988), (211, 938)))
        self.escarpas = []
        # Rampas largas a nordeste e sudoeste conduzem ao único refúgio.
        acessos = {2: tuple(range(8)), 6: tuple(range(8))}
        self.morros = [self.montar_morro(area_central, acessos)]
        # A areia ultrapassa o enquadramento da saída para não terminar em um corte no mar.
        self.eixo_ponte = ((1030, 471), (2400, 250))
        self.ponte = faixa_irregular(self.eixo_ponte, 124, amplitude=8, passo=32)
        self.saida = pygame.Rect(1660, 306, 40, 126)
        self.relevos = []
        self.muros = []
        for a, b in (((315, 791), (315, 750)), ((315, 750), (423, 750)),
                     ((423, 750), (423, 792))):
            inicio = planta(a[0], a[1] - 35)
            fim = planta(b[0], b[1] - 35)
            self.muros.extend(self.blocos_na_linha(inicio, fim, 24))
        self.pedras_ruinas = []
        self.naufragio = pygame.Rect(170, 880, 480, 250)
        self.area_destrocos = self.naufragio.inflate(150, 100)
        self.placas = [
            (pygame.Rect(*planta(x, y), 42, 36), texto)
            for x, y, texto in (
                (462, 1045, 'O descanso dos apóstatas.'),
            )
        ]
        self.placa_esqueletos = self.placas[0][0]
        self.placa_esqueletos.topleft = (974, 948)
        self.pedras_areia = [pygame.Rect(*planta(x, y), 18 + n % 3 * 5, 15 + n % 2 * 5)
                             for n, (x, y) in enumerate((
                                 (205, 843), (245, 745), (470, 727), (548, 819),
                                 (563, 991), (476, 1087), (260, 1130), (193, 1010),
                                 (345, 1143), (517, 1044)))]
        for x, y in ((265, 780), (586, 901), (491, 1121), (278, 1008),
                     (375, 954), (485, 904)):
            px, py = planta(x, y)
            self.pedras_areia.extend(pygame.Rect(px + dx, py + dy, largura, altura)
                                     for dx, dy, largura, altura in
                                     ((-17, 0, 17, 13), (7, -11, 21, 16), (13, 14, 15, 11)))
        self.baus = [pygame.Rect(*planta(356, 724), 65, 40)]
        self.grupo_cruzes = pygame.Rect(865, 742, 260, 194)
        self.cruzes = [pygame.Rect(self.grupo_cruzes.x + deslocamento,
                                   self.grupo_cruzes.bottom - 24, 22, 24)
                       for deslocamento in (38, 121, 204)]
        self.objetos = []
        for n, (x, y) in enumerate(((179, 1030), (450, 753), (492, 779))):
            r = pygame.Rect(*planta(x, y), 42, 54)
            if n == 1:
                base = r.midbottom
                r.size = (54, 42)
                r.midbottom = base
            self.objetos.append(('barril_deitado' if n == 1 else 'barril', r))
        self.objetos.extend(('caixa', pygame.Rect(*planta(x, y), 46, 44))
                            for x, y in ((463, 786), (291, 754)))
        self.arbustos = []
        for x, y, largura, altura in (
            (354, 905, 68, 145), (372, 891, 78, 167), (397, 895, 65, 139),
            (242, 811, 54, 98), (255, 708, 70, 145),
            (526, 752, 50, 90), (556, 805, 67, 139),
            (590, 977, 54, 98),
            (160, 844, 49, 90),
        ):
            px, py = planta(x, y)
            largura = round(largura * 1.8)
            altura = round(altura * 1.8)
            self.objetos.append(('palmeira', pygame.Rect(px-largura//2, py-altura,
                                                        largura, altura)))
        for x, y in ((290, 700), (350, 685), (405, 685), (455, 700)):
            self.arbustos.append(planta(x, y))
        protegidos = [r.inflate(8, 8) for _, r in self.objetos]
        protegidos += self.baus + [self.naufragio, self.grupo_cruzes, self.placa_esqueletos]
        for x, y in ((300, 1008), (475, 1030), (490, 832), (268, 891),
                     (522, 921), (560, 1060), (237, 781), (397, 740)):
            pedra = pygame.Rect(*planta(x, y), 17, 13)
            if not any(pedra.colliderect(r) for r in protegidos + self.pedras_areia):
                self.pedras_areia.append(pedra)
        self.obstaculos = [
            (nome, pygame.Rect(r.centerx-9, r.bottom-12, 18, 12))
            for nome, r in self.objetos
        ] + [('estrutura', r) for r in self.muros + self.baus]
        casco = pygame.Rect(self.naufragio.x + round(self.naufragio.width * .08),
                            self.naufragio.y + round(self.naufragio.height * .56),
                            round(self.naufragio.width * .84),
                            round(self.naufragio.height * .35))
        self.obstaculos.append(('naufragio', casco))
        blocos_escarpa = []
        for a, b in self.escarpas:
            blocos_escarpa.extend(self.blocos_na_linha(a, b, 27))
        self.obstaculos.extend(('escarpa', r) for r in blocos_escarpa)
        centros = sorted({r.center for r in blocos_escarpa}, key=lambda p: (p[1], p[0]))
        self.rochas_escarpa = []
        for x, y in centros:
            largura = 25 + (x + y) % 10
            altura = 24 + (x * 3 + y) % 13
            self.rochas_escarpa.append(pygame.Rect(x - largura // 2, y + 10 - altura,
                                                   largura, altura))
        self.obstaculos.extend(('cruz', r) for r in self.cruzes)
        self.obstaculos.extend((nome, r.inflate(-16, -12)) for nome, r in self.relevos)
        aleatorio = random.Random(21)
        self.textura = [(aleatorio.randrange(self.tamanho[0]), aleatorio.randrange(self.tamanho[1]))
                        for _ in range(950)]
        self.atualizar_mare(agora)
        self.terreno = pygame.Surface(self.tamanho, pygame.SRCALPHA).convert_alpha()
        camera_mapa = Camera(*self.tamanho, *self.tamanho)
        self.desenhar_relevo(self.terreno, camera_mapa)
        desenhar_pedras_pequenas(self.terreno, camera_mapa, self.pedras_areia)
        variantes=('arbusto-tropical-folhas.png','arbusto-tropical-samambaia.png',
                   'arbusto-tropical-baixo.png')
        for n,(x,y) in enumerate(self.arbustos):
            imagem=carregar_sprite_recortado('objects/'+variantes[n%3],(76,52))
            self.terreno.blit(imagem,imagem.get_rect(midbottom=(x,y+16)))
        self.superficie_agua = None
        self.chave_agua = None
        self.ondas_agua = pygame.Surface(self.tamanho, pygame.SRCALPHA).convert_alpha()
        self.ondas_agua.fill((24, 77, 91, 215))
        for y in range(0, self.tamanho[1], 28):
            for x in range(-77, self.tamanho[0], 77):
                inicio = x + y % 63
                pygame.draw.line(self.ondas_agua, (88, 150, 158, 215),
                                 (inicio, y), (inicio + 19, y), 2)
        mascara = pygame.Surface(self.tamanho, pygame.SRCALPHA)
        for morro in self.morros:
            pygame.draw.polygon(mascara, 'white', morro)
        self.mascara_morro = pygame.mask.from_surface(mascara)
        self.camadas_fixas = self.preparar_objetos()
        self.imagem_cruzes = carregar_imagem('objects/cruzes.webp', self.grupo_cruzes.size)
        self.imagens_submersas = {}

    def montar_morro(self, triangulo, acessos):
        contorno = []
        for lado, (a, b) in enumerate(zip(triangulo, triangulo[1:] + triangulo[:1])):
            inicio, fim = pygame.Vector2(a), pygame.Vector2(b)
            normal = (fim - inicio).normalize().rotate(90)
            saliencias = (0, 9, -6, 13, -9, 5, -11, 8, 0)
            borda = [inicio.lerp(fim, i / 8) + normal * desvio
                     for i, desvio in enumerate(saliencias)]
            contorno.extend(tuple(p) for p in borda[:-1])
            for trecho, (p, q) in enumerate(zip(borda, borda[1:])):
                if trecho not in acessos.get(lado, ()):
                    self.escarpas.append((p, q))
        return tuple(contorno)

    @staticmethod
    def blocos_na_linha(a, b, largura):
        inicio, fim = pygame.Vector2(a), pygame.Vector2(b)
        passos = max(1, round(inicio.distance_to(fim) / (largura / 2)))
        blocos = []
        for i in range(passos + 1):
            r = pygame.Rect(0, 0, largura, largura)
            r.center = inicio.lerp(fim, i / passos)
            blocos.append(r)
        return blocos


    def iniciar_mare(self, agora):
        if self.inicio_mare is None:
            self.inicio_mare = agora
            self.atualizar_mare(agora)

    def atualizar_mare(self, agora):
        subida = self.duracao_subida
        decorrido = 0 if self.inicio_mare is None else agora - self.inicio_mare
        ciclo_normal = subida + self.duracao_alta + self.duracao_recuo + self.duracao_baixa
        if self.primeira_mare and self.inicio_mare is not None and decorrido >= 0:
            extra = self.duracao_primeira_subida - subida
            if decorrido < ciclo_normal + extra:
                subida = self.duracao_primeira_subida
            else:
                decorrido -= extra
        fim_alta = subida + self.duracao_alta
        fim_recuo = fim_alta + self.duracao_recuo
        ciclo = fim_recuo + self.duracao_baixa
        if self.inicio_mare is not None and decorrido >= fim_recuo:
            self.passagem_revelada = True
        fase = ciclo if self.inicio_mare is None else decorrido % ciclo
        self.subindo = fase < subida
        self.recuando = fim_alta <= fase < fim_recuo
        self.mare_baixa = fase >= fim_recuo
        if self.subindo:
            self.nivel_agua = fase / subida
            fim = subida
        elif self.recuando:
            self.nivel_agua = (fim_recuo - fase) / self.duracao_recuo
            fim = fim_recuo
        elif self.mare_baixa:
            self.nivel_agua = 0
            fim = ciclo
        else:
            self.nivel_agua = 1
            fim = fim_alta
        self.segundos_restantes = (fim - fase + 999) // 1000

        centro = pygame.Vector2(planta(380, 925))
        self.costa_seca = tuple(tuple(pygame.Vector2(p).lerp(centro, self.nivel_agua))
                                for p in self.costa)
        fracao_seca = 1 - self.nivel_agua
        self.ponte_seca = faixa_irregular(self.eixo_ponte, 124 * fracao_seca,
                                         amplitude=8 * fracao_seca, passo=32)

    def em_terra(self, pes):
        if not pygame.Rect((0, 0), self.tamanho).contains(pes):
            return False
        return all(ponto_no_poligono(p, self.costa)
                   or (self.passagem_revelada and ponto_no_poligono(p, self.ponte))
                   for p in ((pes.left, pes.top), (pes.right - 1, pes.top),
                             (pes.left, pes.bottom - 1), (pes.right - 1, pes.bottom - 1)))

    def no_morro(self, pes):
        x, y = pes.center
        largura, altura = self.mascara_morro.get_size()
        return 0 <= x < largura and 0 <= y < altura and bool(self.mascara_morro.get_at((x,y)))

    def na_agua(self, pes):
        p = pes.center
        if (self.nivel_agua <= 0 or not 0 <= p[0] < self.tamanho[0]
                or not 0 <= p[1] < self.tamanho[1] or self.no_morro(pes)):
            return False
        return ((ponto_no_poligono(p, self.costa) or ponto_no_poligono(p, self.ponte))
                and not ponto_no_poligono(p, self.costa_seca)
                and not ponto_no_poligono(p, self.ponte_seca))

    def placa_proxima(self, corpo):
        return next(((rect, texto) for rect, texto in self.placas
                     if corpo.colliderect(rect.inflate(60, 60))), None)

    def desenhar_terreno(self, tela, camera):
        desenhar_mar(tela, camera)
        if self.passagem_revelada and self.nivel_agua < 1:
            pygame.draw.polygon(tela, COR_AREIA,
                                [camera.pos(*p) for p in self.ponte_seca])
        tela.blit(self.terreno, (-camera.x, -camera.y))

    def desenhar_relevo(self, tela, camera):
        pygame.draw.polygon(tela, COR_AREIA, [camera.pos(*p) for p in self.costa])
        for morro in self.morros:
            self.desenhar_morro(tela, camera, morro)
        for rocha in self.rochas_escarpa:
            self.desenhar_rocha(tela, camera.rect(rocha), rocha.x % 3)
        for nome, relevo in self.relevos:
            r = camera.rect(relevo)
            if nome == 'lajes':
                pygame.draw.polygon(tela, (88, 78, 59),
                                    (r.midleft, r.midtop, r.topright, r.bottomright, r.bottomleft))
                for i in (0, 18, 36):
                    pygame.draw.line(tela, (169, 150, 105), (r.left + 16, r.centery + i // 2),
                                     (r.right - 12, r.top + 8 + i), 5)
            else:
                self.desenhar_rocha(tela, r, 1)
        visivel = tela.get_rect().inflate(14, 0)
        for x, y in self.textura:
            pos = camera.pos(x, y)
            if visivel.collidepoint(pos) and ponto_no_poligono((x, y), self.morros[0]):
                pygame.draw.line(tela, (179, 157, 108), pos, (pos[0] + 6, pos[1]), 2)

    @staticmethod
    def desenhar_rocha(tela, r, variante):
        topo = (r.left + r.width * (2 + variante) // 7, r.top)
        ombro = (r.right - r.width // 6, r.top + r.height // 4)
        crista = (r.centerx, r.top + r.height // 2)
        base = (r.centerx + r.width // 8, r.bottom)
        esquerda = (r.left, r.centery + r.height // 8)
        direita = (r.right, r.bottom - r.height // 4)
        pygame.draw.ellipse(tela, (72, 64, 49),
                            (r.left, r.bottom - r.height // 5, r.width, r.height // 4))
        pygame.draw.polygon(tela, (145, 134, 102), (esquerda, topo, ombro, crista))
        pygame.draw.polygon(tela, (107, 101, 78), (esquerda, crista, base))
        pygame.draw.polygon(tela, (83, 78, 63), (crista, ombro, direita, base))
        pygame.draw.line(tela, (176, 161, 121), topo, ombro, 2)

    @staticmethod
    def desenhar_morro(tela, camera, morro):
        vertices = [pygame.Vector2(p) for p in morro]
        centro = sum(vertices, pygame.Vector2()) / len(vertices)
        pygame.draw.polygon(tela, (99, 87, 61), [camera.pos(*p) for p in vertices])
        for margem, altura, topo in (
            (.10, 22, COR_AREIA),
            (.24, 25, COR_AREIA),
            (.39, 28, COR_AREIA),
        ):
            base = [p.lerp(centro, margem) for p in vertices]
            superficie = [p - pygame.Vector2(0, altura) for p in base]
            for i in range(len(base)):
                cor = ((92, 76, 56), (107, 88, 61), (78, 69, 54))[(i // 8) % 3]
                j = (i + 1) % len(base)
                face = (superficie[i], superficie[j], base[j], base[i])
                pygame.draw.polygon(tela, cor, [camera.pos(*p) for p in face])
                for fracao in (.42, .76):
                    inicio = superficie[i].lerp(base[i], fracao)
                    fim = superficie[j].lerp(base[j], fracao)
                    pygame.draw.line(tela, (134, 112, 77), camera.pos(*inicio),
                                     camera.pos(*fim), 2)
            pygame.draw.polygon(tela, topo, [camera.pos(*p) for p in superficie])
            pygame.draw.lines(tela, (175, 157, 104), True,
                              [camera.pos(*p) for p in superficie], 2)

    def desenhar_chao(self, tela, camera):
        self.desenhar_terreno(tela, camera)

    def preparar_objetos(self):
        camadas = []
        for nome, rect in self.objetos:
            arquivo = 'barril' if nome == 'barril_deitado' else nome
            rotacao = 90 if nome == 'barril_deitado' else 0
            imagem = carregar_imagem(f'objects/{arquivo}.png', rect.size, rotacao)
            parte_submersa = .22 if nome == 'palmeira' else 1
            camadas.append((rect.bottom, imagem, rect.topleft, parte_submersa))
        for muro in self.muros + self.pedras_ruinas:
            imagem = pygame.Surface(muro.size, pygame.SRCALPHA)
            r = imagem.get_rect()
            pygame.draw.rect(imagem, (83, 77, 65), r)
            pygame.draw.rect(imagem, (130, 121, 101), r.inflate(-8, -8))
            pygame.draw.line(imagem, (158, 147, 121), (4, 4), (r.right - 5, 4), 3)
            camadas.append((muro.bottom, imagem, muro.topleft, 1))
        imagem = carregar_imagem('objects/naufragio.webp', self.naufragio.size)
        camadas.append((self.naufragio.bottom, imagem, self.naufragio.topleft, 1))
        for placa, _ in self.placas:
            imagem = carregar_sprite_recortado('objects/placa-envelhecida.png', placa.size)
            camadas.append((placa.bottom, imagem, placa.topleft, 1))
        for bau in self.baus:
            visual = pygame.Rect(0, 0, bau.width, bau.height + 12)
            visual.midbottom = bau.midbottom
            imagem = carregar_imagem('objects/bau-quebrado.webp', visual.size)
            camadas.append((bau.bottom, imagem, visual.topleft, 1))
        return camadas

    def desenhar_objetos(self, tela, camera, personagem=None):
        camadas = list(self.camadas_fixas)
        if not self.na_agua(pygame.Rect(self.grupo_cruzes.midbottom, (1, 1))):
            camadas.append((self.grupo_cruzes.bottom, self.imagem_cruzes,
                            self.grupo_cruzes.topleft, 1))
        if personagem is not None:
            imagem, posicao, profundidade = personagem
            camadas.append((profundidade, imagem, posicao, .18))
        if self.nivel_agua:
            self.desenhar_agua(tela, camera)
        for profundidade, imagem, posicao, parte_submersa in sorted(camadas, key=lambda camada: camada[0]):
            destino = camera.rect(imagem.get_rect(topleft=posicao))
            if not tela.get_rect().colliderect(destino):
                continue
            base = pygame.Rect(posicao[0] + imagem.get_width() // 2, profundidade - 1, 1, 1)
            if self.na_agua(base):
                chave = (id(imagem), parte_submersa)
                if chave not in self.imagens_submersas:
                    molhada = imagem.copy()
                    altura = round(imagem.get_height() * parte_submersa)
                    faixa = pygame.Rect(0, imagem.get_height() - altura, imagem.get_width(), altura)
                    molhada.fill((90, 145, 165), faixa, special_flags=pygame.BLEND_RGB_MULT)
                    self.imagens_submersas[chave] = (imagem, molhada)
                imagem = self.imagens_submersas[chave][1]
            tela.blit(imagem, destino)

    def draw(self, tela, camera):
        self.desenhar_chao(tela, camera)
        self.desenhar_objetos(tela, camera)

    def desenhar_agua(self, tela, camera):
        chave = (self.nivel_agua, camera.x, camera.y, tela.get_size())
        if chave == self.chave_agua:
            tela.blit(self.superficie_agua, (0, 0))
            return
        if self.superficie_agua is None or self.superficie_agua.get_size() != tela.get_size():
            self.superficie_agua = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
        agua = self.superficie_agua
        agua.fill((0, 0, 0, 0))
        pygame.draw.polygon(agua, (255, 255, 255, 255), [camera.pos(*p) for p in self.costa])
        secos = self.morros
        if self.nivel_agua < 1:
            secos = (*secos, self.costa_seca, self.ponte_seca)
        for seco in secos:
            pygame.draw.polygon(agua, (0, 0, 0, 0), [camera.pos(*p) for p in seco])
        agua.blit(self.ondas_agua, (-camera.x, -camera.y), special_flags=pygame.BLEND_RGBA_MIN)
        self.chave_agua = chave
        tela.blit(agua, (0, 0))

    def desenhar_respingos(self, tela, pes, agora):
        for atraso, deslocamento in ((0, -8), (160, 8)):
            raio = 4 + ((agora + atraso) % 360) // 23
            centro = (pes.centerx + deslocamento, pes.bottom - 4)
            pygame.draw.ellipse(tela, (153, 220, 224),
                                pygame.Rect(0, 0, raio * 2, raio).move(
                                    centro[0] - raio, centro[1] - raio // 2), 1)
