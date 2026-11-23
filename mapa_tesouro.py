"""Revelação animada do mapa, usando a arte já coletada no jogo."""
import pygame
from asset_loader import carregar_imagem
from menu_principal import MenuPrincipal

TEMPO_ENCAIXE_MS = 1600
TEMPO_LIBERAR_MS = 1950


class TelaMapaTesouro(MenuPrincipal):
    opcoes = ('Continuar',)
    acoes = ('continuar',)
    acao_escape = 'continuar'

    def __init__(self, tamanho):
        super().__init__(tamanho, 'derrota.png', '')
        self.botoes[0].center = (tamanho[0]//2, tamanho[1]-52)
        self.fonte_titulo = pygame.font.SysFont('georgia', 49, bold=True)
        self.fonte_frase = pygame.font.SysFont('georgia', 25)
        original = carregar_imagem('objects/mapa-completo.png')
        visivel = original.subsurface(original.get_bounding_rect(min_alpha=128))
        escala = min(430/visivel.get_width(), 340/visivel.get_height())
        self.mapa = pygame.transform.smoothscale(visivel,
            (round(visivel.get_width()*escala),round(visivel.get_height()*escala)))
        w,h = self.mapa.get_size()
        self.recorte = [(w//2 + (9 if n%2 else -9),round(n*h/12)) for n in range(13)]
        poligono = [(0,0),*self.recorte,(0,h)]
        mascara = pygame.Surface((w,h),pygame.SRCALPHA)
        pygame.draw.polygon(mascara,'white',poligono)
        self.esquerda = self.mapa.copy()
        self.esquerda.blit(mascara,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
        mascara.fill('white')
        pygame.draw.polygon(mascara,(0,0,0,0),poligono)
        self.direita = self.mapa.copy()
        self.direita.blit(mascara,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
        self.inicio = 0

    def iniciar(self, agora):
        self.inicio = agora
        self.selecionado = 0

    def pronto(self):
        return pygame.time.get_ticks()-self.inicio >= TEMPO_LIBERAR_MS

    def evento(self, evento):
        if not self.pronto():return None
        self.selecionado = 0
        return super().evento(evento)

    def posicoes_metades(self, agora):
        progresso=max(0,min(1,(agora-self.inicio)/TEMPO_ENCAIXE_MS))
        restante=(1-progresso)**3
        rect=self.mapa.get_rect(center=(self.tamanho[0]//2,330))
        return (rect.move(round(-155*restante),round(12*restante)),
                rect.move(round(155*restante),round(-12*restante)))

    def desenhar(self, tela):
        self.selecionado=0 if self.pronto() else -1
        super().desenhar(tela)
        agora=pygame.time.get_ticks()
        def central(texto,fonte,y,cor,alpha=255):
            sombra=fonte.render(texto,True,(3,8,10));letras=fonte.render(texto,True,cor)
            sombra.set_alpha(alpha);letras.set_alpha(alpha)
            cx=self.tamanho[0]//2
            tela.blit(sombra,sombra.get_rect(center=(cx+2,y+2)))
            tela.blit(letras,letras.get_rect(center=(cx,y)))
        central('Mapa do Tesouro',self.fonte_titulo,69,(235,200,130))
        central('Você encontrou a metade que faltava!',self.fonte_frase,128,(255,255,255))
        esquerda,direita=self.posicoes_metades(agora)
        if agora-self.inicio>=TEMPO_ENCAIXE_MS:
            tela.blit(self.mapa,esquerda)
        else:
            tela.blit(self.esquerda,esquerda)
            tela.blit(self.direita,direita)
        alpha=round(255*max(0,min(1,(agora-self.inicio-TEMPO_ENCAIXE_MS)/350)))
        central('Localização do tesouro descoberta',self.fonte_frase,551,(245,216,159),alpha)
