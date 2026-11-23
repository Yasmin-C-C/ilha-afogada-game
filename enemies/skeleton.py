import pygame
import heapq
from enemies.animacoes import carregar_animacoes_escaladas, DIRECOES, ANCORA_X
from colisoes import bloqueia_movimento

INTERVALO_CAMINHADA_MS = 120

class Skeleton:
    sprite_nome = 'skeleton'

    def __init__(
        self,
        x,
        y,
        lado="centro",
        dropaFrasco=False,
        patrulha=None,
        altura_visual=110
    ):
        self.x = x
        self.y = y

        self.width = 40
        self.height = 60

        self.rect = pygame.Rect(
            self.x,
            self.y,
            self.width,
            self.height
        )

        self.vida = 3
        self.vivo = True
        self.speed = 1.5
        self.movimento_fracionario = pygame.Vector2()
        self.detected = 200
        self.dist_ataque = 45
        self.last_atack = 0
        self.cooldown = 1000
        self.duracao_atordoamento = 240
        self.lado = lado
        self.direcao = 'baixo'
        self.dropaFrasco = dropaFrasco

        self.patrulha = (
            patrulha
            if patrulha
            else [(x, y)]
        )

        self.ponto_pat = 0
        self.caminho_desvio = []
        self.tentativa_desvio = -1000

        self.sprite_altura = altura_visual

        self.animacoes = carregar_animacoes_escaladas(self.sprite_nome, altura_visual)
        self.image_frente = self.animacoes['parada']['frente'][0]
        self.image_costas = self.animacoes['parada']['costas'][0]
        self.image_direita = self.animacoes['parada']['direita'][0]
        self.image_esquerda = self.animacoes['parada']['esquerda'][0]
        self.image = self.image_frente
        self.ao_som = None
        self.reiniciar_animacoes()

    def visual(self):
        agora = pygame.time.get_ticks()
        direcao = self.direcao
        if not self.vivo:
            acao, inicio, passo = 'derrota', self.inicio_derrota, 120
        elif agora - self.inicio_dano < self.duracao_atordoamento:
            acao, inicio, passo = 'dano', self.inicio_dano, max(1,self.duracao_atordoamento//2)
        elif self.ataque_em_andamento(agora):
            acao, inicio, passo = 'ataque', self.inicio_ataque, 100
            direcao = self.direcao_ataque
        else:
            acao = 'caminhada' if agora - self.ultima_movimentacao < 90 else 'parada'
            chave = (acao, direcao)
            if chave != self.animacao_atual:
                self.animacao_atual = chave
                self.inicio_animacao = agora
            inicio, passo = self.inicio_animacao, INTERVALO_CAMINHADA_MS if acao == 'caminhada' else 200
        quadros = self.animacoes[acao][DIRECOES[direcao]]
        indice = max(0, (agora - (inicio if inicio is not None else agora)) // passo)
        self.quadro_atual = (indice % len(quadros) if acao in ('parada', 'caminhada')
                             else min(len(quadros) - 1, indice))
        self.acao_visual = acao
        self.image = quadros[self.quadro_atual]
        return self.image, round(ANCORA_X * self.sprite_altura / 110)

    def reiniciar_animacoes(self):
        self.ultimo_som_passo = -10000
        self.inicio_ataque = -10000
        self.inicio_dano = -10000
        self.inicio_derrota = None
        self.ultima_movimentacao = -10000
        self.direcao_ataque = self.direcao
        self.impacto_resolvido = True
        self.animacao_atual = None
        self.inicio_animacao = pygame.time.get_ticks()
        self.quadro_atual = 0

    def ataque_em_andamento(self, agora=None):
        agora = pygame.time.get_ticks() if agora is None else agora
        return self.vivo and 0 <= agora - self.inicio_ataque < 400

    def em_derrota(self):
        return (not self.vivo and self.inicio_derrota is not None
                and pygame.time.get_ticks() - self.inicio_derrota < 720)

    def recebeDano(self, quantidade=1):

        if not self.vivo:
            return
        self.vida = max(0, self.vida - quantidade)
        self.inicio_dano = pygame.time.get_ticks()
        self.inicio_ataque = -10000
        self.impacto_resolvido = True

        if self.vida <= 0:
            self.vida = 0
            self.vivo = False
            self.inicio_derrota = self.inicio_dano

        if self.ao_som and self.sprite_nome in ('skeleton', 'pirata'):
            self.ao_som(self.sprite_nome + ('_dano' if self.vivo else '_derrota'))


    def tentar_mover(
        self,
        dx,
        dy,
        kia,
        skeletons
    ):

        if (not self.vivo or self.ataque_em_andamento()
                or pygame.time.get_ticks() - self.inicio_dano < self.duracao_atordoamento):
            return
        total_x = dx + self.movimento_fracionario.x if dx else 0
        total_y = dy + self.movimento_fracionario.y if dy else 0
        passo_x, passo_y = int(total_x), int(total_y)
        if dx:self.movimento_fracionario.x = total_x - passo_x
        if dy:self.movimento_fracionario.y = total_y - passo_y
        new = self.rect.move(passo_x, passo_y)

        kia_clld = new.colliderect(
            kia.bodyRect
        )

        skeleton_clld = any(
            outro != self
            and outro.vivo
            and new.colliderect(outro.rect)
            for outro in skeletons
        )

        pes = pygame.Rect(new.x + 5, new.bottom - 12, 30, 12)
        corpo = self.corpo_em(new)
        obter_obstaculos = getattr(self, 'obter_obstaculos', None)
        cenario_clld = (obter_obstaculos is not None
                        and bloqueia_movimento(pes, corpo, obter_obstaculos()))
        em_terra = getattr(self, 'em_terra', None)
        if em_terra is not None and not em_terra(pes):
            cenario_clld = True

        if not kia_clld and not skeleton_clld and not cenario_clld:
            moveu = new.topleft != self.rect.topleft
            self.rect = new
            agora = pygame.time.get_ticks()
            if (moveu and self.sprite_nome == 'skeleton' and self.ao_som
                    and agora - self.ultimo_som_passo >= 480):
                self.ultimo_som_passo = agora
                self.ao_som('skeleton_ossos')
            if dx or dy:
                self.ultima_movimentacao = pygame.time.get_ticks()

            self.atualizar_direcao(
                dx,
                dy
            )
        else:
            if dx:self.movimento_fracionario.x = 0
            if dy:self.movimento_fracionario.y = 0

    def corpo_em(self, rect):
        altura = self.sprite_altura - 10
        return pygame.Rect(rect.centerx - 22, rect.bottom - altura, 44, altura)


    def seguir_desvio(self, kia, inimigos):
        if not self.caminho_desvio:
            return False
        alvo = self.caminho_desvio[0]
        dx, dy = alvo[0] - self.rect.centerx, alvo[1] - self.rect.centery
        if abs(dx) <= 3 and abs(dy) <= 3:
            self.caminho_desvio.pop(0)
            return True
        anterior = self.rect.copy()
        if abs(dx) > 2:
            self.tentar_mover(self.speed if dx > 0 else -self.speed, 0, kia, inimigos)
        if abs(dy) > 2:
            self.tentar_mover(0, self.speed if dy > 0 else -self.speed, kia, inimigos)
        if self.rect == anterior:
            self.caminho_desvio.clear()
        return True

    def planejar_desvio(self, alvo):
        agora = pygame.time.get_ticks()
        if agora - self.tentativa_desvio < 500:
            return
        self.tentativa_desvio = agora
        obstaculos = self.obter_obstaculos()
        origem = pygame.Vector2(self.rect.center)
        destino = pygame.Vector2(alvo)
        passo = 24
        limite = pygame.Rect(min(origem.x, destino.x) - 192,
                             min(origem.y, destino.y) - 192,
                             abs(origem.x - destino.x) + 384,
                             abs(origem.y - destino.y) + 384)
        # Inclui toda a extensão possível do corpo e dos pés dentro da busca.
        # Obstáculos fora dessa margem não podem bloquear nenhum nó avaliado.
        area_busca = limite.inflate(128, self.sprite_altura * 2 + 80)
        obstaculos = [(tipo, rect) for tipo, rect in obstaculos
                      if area_busca.colliderect(rect)]
        def ponto(no):
            return (round(origem.x + no[0] * passo), round(origem.y + no[1] * passo))
        def livre(pos):
            x, y = pos
            pes = pygame.Rect(x - 15, y + 18, 30, 12)
            corpo = self.corpo_em(pygame.Rect(x - 20, y - 30, 40, 60))
            return (limite.collidepoint(pos) and self.em_terra(pes)
                    and not bloqueia_movimento(pes, corpo, obstaculos))
        def distancia(no):
            x, y = ponto(no)
            return (abs(x - destino.x) + abs(y - destino.y)) / passo
        fila = [(distancia((0, 0)), 0, (0, 0))]
        custos, anteriores = {(0, 0): 0}, {}
        while fila and len(custos) < 5000:
            _, custo, no = heapq.heappop(fila)
            if custo != custos[no]:
                continue
            if no != (0, 0) and pygame.Vector2(ponto(no)).distance_to(destino) <= 30:
                caminho = []
                while no != (0, 0):
                    caminho.append(ponto(no))
                    no = anteriores[no]
                self.caminho_desvio = list(reversed(caminho))
                return
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                vizinho = (no[0] + dx, no[1] + dy)
                if custo + 1 >= custos.get(vizinho, float('inf')):
                    continue
                inicio, fim = pygame.Vector2(ponto(no)), pygame.Vector2(ponto(vizinho))
                if not all(livre(inicio.lerp(fim, t)) for t in (.25, .5, .75, 1)):
                    continue
                custos[vizinho] = custo + 1
                anteriores[vizinho] = no
                heapq.heappush(fila, (custo + 1 + distancia(vizinho), custo + 1, vizinho))

    def atualizar_direcao(
        self,
        dx,
        dy
    ):

        self.direcao = ('direita' if dx > 0 else 'esquerda') if abs(dx) > abs(dy) else ('baixo' if dy > 0 else 'cima')

        if abs(dx) > abs(dy):

            if dx > 0 and self.image_direita:
                self.image = self.image_direita

            elif dx < 0 and self.image_esquerda:
                self.image = self.image_esquerda

        else:

            if dy > 0 and self.image_frente:
                self.image = self.image_frente

            elif dy < 0 and self.image_costas:
                self.image = self.image_costas


    def patrulhar(
        self,
        kia,
        skeletons
    ):

        if not self.vivo:
            return

        alvo_x, alvo_y = self.patrulha[
            self.ponto_pat
        ]

        dist_x = alvo_x - self.rect.centerx
        dist_y = alvo_y - self.rect.centery

        if abs(dist_x) <= 4 and abs(dist_y) <= 4:

            self.ponto_pat = (
                self.ponto_pat + 1
            ) % len(self.patrulha)

            return

        if abs(dist_x) > 2:

            if dist_x > 0:

                self.tentar_mover(
                    self.speed,
                    0,
                    kia,
                    skeletons
                )

            else:

                self.tentar_mover(
                    -self.speed,
                    0,
                    kia,
                    skeletons
                )

        if abs(dist_y) > 2:

            if dist_y > 0:

                self.tentar_mover(
                    0,
                    self.speed,
                    kia,
                    skeletons
                )

            else:

                self.tentar_mover(
                    0,
                    -self.speed,
                    kia,
                    skeletons
                )


    def seguir(
        self,
        kia,
        skeletons
    ):

        if not self.vivo:
            return

        kia_x = (
            kia.bodyRect.centerx
            - self.rect.centerx
        )

        kia_y = (
            kia.bodyRect.centery
            - self.rect.centery
        )

        distancia_kia = (
            kia_x ** 2
            + kia_y ** 2
        ) ** 0.5

        if distancia_kia > self.detected:

            self.patrulhar(
                kia,
                skeletons
            )

            return

        alvo_x = kia.bodyRect.centerx
        alvo_y = kia.bodyRect.centery

        if self.lado == "esquerda":
            alvo_x -= 55

        elif self.lado == "direita":
            alvo_x += 55

        elif self.lado == "baixo":
            alvo_y += 65

        dist_x = alvo_x - self.rect.centerx
        dist_y = alvo_y - self.rect.centery

        dist = (
            dist_x ** 2
            + dist_y ** 2
        ) ** 0.5

        if dist > self.dist_ataque:

            if dist_x > 3:

                self.tentar_mover(
                    self.speed,
                    0,
                    kia,
                    skeletons
                )

            elif dist_x < -3:

                self.tentar_mover(
                    -self.speed,
                    0,
                    kia,
                    skeletons
                )

            if dist_y > 3:

                self.tentar_mover(
                    0,
                    self.speed,
                    kia,
                    skeletons
                )

            elif dist_y < -3:

                self.tentar_mover(
                    0,
                    -self.speed,
                    kia,
                    skeletons
                )


    def atacar(self, kia, pode_atingir=True):
        if not self.vivo or not kia.viva:
            return
        agora = pygame.time.get_ticks()
        alcance = self.rect.inflate(30, 30).colliderect(kia.bodyRect)
        # Resolve o golpe mesmo durante a esquiva: ele não fica pendente.
        if self.ataque_em_andamento(agora):
            if not self.impacto_resolvido and agora - self.inicio_ataque >= 100:
                self.impacto_resolvido = True
                if pode_atingir and alcance:
                    kia.recebeDano()
            return
        self.impacto_resolvido = True
        if (alcance and agora - self.last_atack >= self.cooldown
                and agora - self.inicio_dano >= self.duracao_atordoamento):
            dx = kia.bodyRect.centerx - self.rect.centerx
            dy = kia.bodyRect.centery - self.rect.centery
            self.atualizar_direcao(dx, dy)
            self.direcao_ataque = self.direcao
            self.inicio_ataque = self.last_atack = agora
            self.impacto_resolvido = False
            if self.sprite_nome == 'skeleton' and self.ao_som:
                self.ao_som('skeleton_espada')
            elif self.sprite_nome == 'pirata' and self.ao_som:
                self.ao_som('pirata_ataque')


    def draw(
        self,
        screen,
        camera
    ):

        imagem, ancora = self.visual()
        if imagem:

            draw_x = (
                self.rect.centerx
                - ancora
            )

            draw_y = (
                self.rect.bottom
                - imagem.get_height()
            )

            screen.blit(
                imagem,
                camera.pos(
                    draw_x,
                    draw_y
                )
            )

        else:

            r = camera.rect(
                self.rect
            )

            pygame.draw.rect(
                screen,
                (205, 205, 185),
                r,
                border_radius=4
            )

            pygame.draw.circle(
                screen,
                (230, 225, 200),
                (
                    r.centerx,
                    r.y + 12
                ),
                11
            )

            pygame.draw.circle(
                screen,
                (45, 35, 35),
                (
                    r.centerx - 4,
                    r.y + 11
                ),
                2
            )

            pygame.draw.circle(
                screen,
                (45, 35, 35),
                (
                    r.centerx + 4,
                    r.y + 11
                ),
                2
            )

            pygame.draw.line(
                screen,
                (170, 165, 150),
                (
                    r.centerx,
                    r.y + 23
                ),
                (
                    r.centerx,
                    r.bottom - 8
                ),
                5
            )
