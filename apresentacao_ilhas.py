"""Cartelas de descoberta, compartilhando a identidade das telas do jogo."""
import pygame
from asset_loader import ASSETS


DURACAO_DESCOBERTA_MS = 4150
FADE_SAIDA_MS = 450
FADE_CARTELA_MS = 350


class ApresentacoesIlhas:
    textos = {
        'macacos': ('Ilha dos Macacos descoberta!', 'Existe caminho de volta para casa?'),
        'caveira': ('Ilha da Caveira descoberta!', 'Em busca do tesouro escondido...'),
    }

    def __init__(self, tamanho):
        self.tamanho = tamanho
        self.fundos = {}
        self.fontes_titulo = {}
        self.fonte_frase = pygame.font.SysFont('georgia', 27, italic=True)
        for nome, (titulo, _) in self.textos.items():
            caminho = ASSETS / 'menu' / f'descoberta-{nome}.png'
            if caminho.is_file():
                original = pygame.image.load(str(caminho)).convert()
                escala = max(tamanho[0]/original.get_width(), tamanho[1]/original.get_height())
                self.fundos[nome] = pygame.transform.smoothscale(original,
                    (round(original.get_width()*escala),round(original.get_height()*escala)))
            tamanho_fonte = 48
            while True:
                fonte = pygame.font.SysFont('georgia', tamanho_fonte, bold=True)
                if fonte.size(titulo)[0] <= tamanho[0]-120:break
                tamanho_fonte -= 1
            self.fontes_titulo[nome] = fonte
        self.sombra = pygame.Surface(tamanho, pygame.SRCALPHA)
        for y in range(tamanho[1]):
            alpha=round(105*max(0,min(1,(y-tamanho[1]*.38)/(tamanho[1]*.42))))
            pygame.draw.line(self.sombra,(5,15,19,alpha),(0,y),(tamanho[0],y))

    def desenhar(self, tela, nome):
        tela.fill((20,48,37) if nome=='macacos' else (10,23,30))
        fundo=self.fundos.get(nome)
        if fundo is not None:tela.blit(fundo,fundo.get_rect(center=tela.get_rect().center))
        tela.blit(self.sombra,(0,0))
        titulo,frase=self.textos[nome]
        cx=self.tamanho[0]//2
        def central(texto, fonte, y, cor):
            sombra=fonte.render(texto,True,(4,12,14))
            imagem=fonte.render(texto,True,cor)
            tela.blit(sombra,sombra.get_rect(center=(cx+2,y+3)))
            tela.blit(imagem,imagem.get_rect(center=(cx,y)))
        central(titulo,self.fontes_titulo[nome],round(self.tamanho[1]*.64),(244,220,165))
        y=round(self.tamanho[1]*.705)
        pygame.draw.line(tela,(188,155,92),(cx-180,y),(cx-14,y),1)
        pygame.draw.line(tela,(188,155,92),(cx+14,y),(cx+180,y),1)
        pygame.draw.polygon(tela,(226,194,126),[(cx,y-5),(cx+5,y),(cx,y+5),(cx-5,y)])
        central(frase,self.fonte_frase,round(self.tamanho[1]*.775),(255,255,255))
