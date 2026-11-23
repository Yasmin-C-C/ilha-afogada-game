"""Menu principal: navegação por teclado e mouse com foco visível."""
import pygame

from asset_loader import ASSETS


class MenuPrincipal:
    opcoes = ('Jogar', 'Sair')
    acoes = ('jogar', 'sair')
    acao_escape = 'sair'

    def __init__(self, tamanho, arquivo_fundo='menu-principal.png', titulo_fallback='A Ilha Afogada'):
        self.tamanho = tamanho
        self.titulo_fallback = titulo_fallback
        self.selecionado = 0
        self.ao_som = None
        largura, altura = tamanho
        self.botoes = [pygame.Rect(0, 0, 300, 62) for _ in self.opcoes]
        for botao, y in zip(self.botoes, (.70, .82)):
            botao.center = (largura // 2, round(altura * y))
        self.fonte = pygame.font.SysFont('georgia', 31, bold=True)
        self.fonte_titulo = pygame.font.SysFont('georgia', 64, bold=True)
        self.fundo = None
        caminho = ASSETS / 'menu' / arquivo_fundo
        if caminho.is_file():
            original = pygame.image.load(str(caminho)).convert()
            escala = max(largura / original.get_width(), altura / original.get_height())
            self.fundo = pygame.transform.smoothscale(original,
                (round(original.get_width() * escala), round(original.get_height() * escala)))

    def evento(self, evento):
        if evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_UP, pygame.K_DOWN):
                anterior = self.selecionado
                self.selecionado = (self.selecionado + (1 if evento.key == pygame.K_DOWN else -1)) % len(self.opcoes)
                if self.ao_som and anterior != self.selecionado:self.ao_som('menu_selecao')
            elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.ao_som:self.ao_som('menu_confirmar')
                return self.acoes[self.selecionado]
            elif evento.key == pygame.K_ESCAPE:
                if self.ao_som:self.ao_som('menu_confirmar')
                return self.acao_escape
        elif evento.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
            for indice, botao in enumerate(self.botoes):
                if botao.collidepoint(evento.pos):
                    if evento.type == pygame.MOUSEMOTION or evento.button == 1:
                        anterior = self.selecionado
                        self.selecionado = indice
                        if self.ao_som and anterior != indice:self.ao_som('menu_selecao')
                    if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                        if self.ao_som:self.ao_som('menu_confirmar')
                        return self.acoes[indice]
        return None

    def desenhar(self, tela):
        tela.fill((10, 24, 32))
        if self.fundo is not None:
            tela.blit(self.fundo, self.fundo.get_rect(center=tela.get_rect().center))
        elif self.titulo_fallback:
            titulo = self.fonte_titulo.render(self.titulo_fallback, True, (210, 176, 112))
            tela.blit(titulo, titulo.get_rect(center=(self.tamanho[0] // 2, 230)))
        self.desenhar_botoes(tela)

    def desenhar_botoes(self, tela):
        for indice, (rotulo, rect) in enumerate(zip(self.opcoes, self.botoes)):
            ativo = indice == self.selecionado
            ouro = (223, 186, 116) if ativo else (112, 93, 65)
            pygame.draw.rect(tela, (4, 10, 14), rect.move(0, 5), border_radius=8)
            pontos = [(rect.left+16,rect.top), (rect.right-16,rect.top),
                      (rect.right,rect.centery), (rect.right-16,rect.bottom),
                      (rect.left+16,rect.bottom), (rect.left,rect.centery)]
            pygame.draw.polygon(tela, (72, 51, 33) if ativo else (30, 29, 28), pontos)
            pygame.draw.polygon(tela, ouro, pontos, 2 if ativo else 1)
            interno = rect.inflate(-18, -12)
            pygame.draw.line(tela, ouro, interno.topleft, interno.topright, 1)
            pygame.draw.line(tela, ouro, interno.bottomleft, interno.bottomright, 1)
            for x in (rect.left+24, rect.right-24):
                pygame.draw.circle(tela, ouro, (x, rect.centery), 3)
            sombra = self.fonte.render(rotulo, True, (8, 10, 10))
            letras = self.fonte.render(rotulo, True, (255, 238, 202) if ativo else (184, 177, 158))
            tela.blit(sombra, sombra.get_rect(center=(rect.centerx+1,rect.centery+2)))
            tela.blit(letras, letras.get_rect(center=rect.center))
            if ativo:
                x, y = rect.left-22, rect.centery
                pygame.draw.polygon(tela, ouro, [(x-8,y-7),(x+2,y),(x-8,y+7)])


class MenuDerrota(MenuPrincipal):
    opcoes = ('Renascer', 'Menu')
    acoes = ('renascer', 'menu')
    acao_escape = 'menu'

    def __init__(self, tamanho):
        super().__init__(tamanho, 'derrota.png', '')
        self.fonte_titulo = pygame.font.SysFont('georgia', 57, bold=True)

    def desenhar(self, tela):
        super().desenhar(tela)
        centro = (self.tamanho[0]//2, round(self.tamanho[1]*.42))
        sombra = self.fonte_titulo.render('Você foi derrotado!', True, (3, 9, 12))
        letras = self.fonte_titulo.render('Você foi derrotado!', True, (224, 192, 134))
        tela.blit(sombra, sombra.get_rect(center=(centro[0]+2,centro[1]+3)))
        tela.blit(letras, letras.get_rect(center=centro))
        y=centro[1]+57
        pygame.draw.line(tela,(145,115,66),(centro[0]-150,y),(centro[0]-14,y),1)
        pygame.draw.line(tela,(145,115,66),(centro[0]+14,y),(centro[0]+150,y),1)
        pygame.draw.polygon(tela,(224,192,134),[(centro[0],y-6),(centro[0]+6,y),
                                             (centro[0],y+6),(centro[0]-6,y)])
