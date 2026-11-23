"""Partida de Kia em busca do tesouro após concluir a terceira ilha."""
import pygame

from menu_principal import MenuPrincipal


class TelaContinuacao(MenuPrincipal):
    opcoes = ('Voltar ao menu',)
    acoes = ('menu',)
    acao_escape = 'menu'

    def __init__(self, tamanho):
        super().__init__(tamanho, 'continuacao-aventura.png', '')
        largura, altura = tamanho
        self.botoes[0].size = (340, 62)
        self.botoes[0].center = (largura // 2, round(altura * .92))
        fonte_titulo = pygame.font.SysFont('georgia', 48, bold=True)
        fonte_mensagem = pygame.font.SysFont('georgia', 24)
        fonte_fim = pygame.font.SysFont('georgia', 30, bold=True)
        fonte_creditos = pygame.font.SysFont('georgia', 22)
        linhas = (
            ('Que novas aventuras nos aguardam?', .115, fonte_titulo),
            ('O mapa completo revela a localização exata do tesouro!', .205, fonte_mensagem),
            ('Fim de Gameplay', .76, fonte_fim),
            ('Criado e produzido por Yasmin Costa', .825, fonte_creditos),
        )
        self.linhas = tuple(
            (fonte.render(texto, True, (255, 255, 255)),
             fonte.render(texto, True, (3, 9, 12)),
             (largura // 2, round(altura * y)))
            for texto, y, fonte in linhas
        )

    def desenhar(self, tela):
        super().desenhar(tela)
        for letras, sombra, centro in self.linhas:
            tela.blit(sombra, sombra.get_rect(center=(centro[0] + 2, centro[1] + 3)))
            tela.blit(letras, letras.get_rect(center=centro))
