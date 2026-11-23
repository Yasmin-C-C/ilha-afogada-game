from functools import lru_cache

import pygame

from asset_loader import carregar_imagem, carregar_sprite_recortado


class HUD:
    ouro = (193, 159, 91)
    texto_claro = (255, 255, 255)
    discreto = (159, 178, 172)

    def __init__(self):
        self.fontes = {
            'pequena': pygame.font.Font(None, 19),
            'corpo': pygame.font.Font(None, 24),
            'titulo': pygame.font.Font(None, 27),
            'fala': pygame.font.Font(None, 32),
        }

    @lru_cache(maxsize=256)
    def renderizar(self, texto, estilo='corpo', cor=texto_claro):
        fonte = self.fontes[estilo]
        letras = fonte.render(texto, True, cor)
        imagem = pygame.Surface((letras.get_width()+2, letras.get_height()+2), pygame.SRCALPHA)
        imagem.blit(fonte.render(texto, True, (12, 20, 23)), (2, 2))
        imagem.blit(letras, (0, 0))
        return imagem

    def texto(self, tela, texto, posicao, estilo='corpo', cor=texto_claro):
        tela.blit(self.renderizar(texto, estilo, cor), posicao)

    def linhas(self, texto, largura, estilo='corpo'):
        linhas = []
        linha = ''
        for palavra in texto.split():
            tentativa = (linha + ' ' + palavra).strip()
            if linha and self.fontes[estilo].size(tentativa)[0] > largura:
                linhas.append(linha)
                linha = palavra
            else:
                linha = tentativa
        if linha:
            linhas.append(linha)
        return linhas

    def desenhar(self, tela, vida, vida_maxima, itens, objetivo, mare=None):
        self.texto(tela, 'VIDA', (36, 32), 'pequena')
        self.texto(tela, f'{vida} / {vida_maxima}', (208, 32), 'pequena')
        barra = pygame.Rect(36, 58, 238, 18)
        pygame.draw.rect(tela, (57, 37, 37), barra, border_radius=5)
        preenchida = barra.copy()
        preenchida.width = round(barra.width * max(0, min(1, vida / max(1, vida_maxima))))
        if preenchida.width:
            pygame.draw.rect(tela, (179, 68, 61), preenchida, border_radius=5)
        pygame.draw.rect(tela, (115, 91, 65), barra, 1, border_radius=5)

        largura_objetivo = tela.get_width() - 690
        linhas = self.linhas(objetivo, largura_objetivo-32)
        for i, linha in enumerate(linhas):
            imagem = self.renderizar(linha)
            tela.blit(imagem, imagem.get_rect(midtop=(tela.get_width()//2, 49+i*25)))

        x_itens = tela.get_width()-368
        centro_itens = round(x_itens + 45 + 81 * (max(1, len(itens))-1) / 2)
        titulo_itens = self.renderizar('ITENS', 'pequena')
        tela.blit(titulo_itens, titulo_itens.get_rect(midtop=(centro_itens, 32)))
        for i, (tipo, legenda) in enumerate(itens):
            x = x_itens + 14 + i*81
            area = pygame.Rect(x+14, 53, 34, 32)
            if tipo == 'armadura':
                tela.blit(carregar_sprite_recortado('objects/armadura.png',area.size),area)
            else:
                arquivo = {'espada': 'espada', 'mapa': 'mapa1', 'chave': 'chave'}[tipo]
                tela.blit(carregar_imagem(f'objects/{arquivo}.png', area.size), area)
            imagem = self.renderizar(legenda, 'pequena')
            tela.blit(imagem, imagem.get_rect(center=(x+32, 98)))

        if mare:
            estado, segundos = mare
            self.texto(tela, estado, (36, 139))
            if segundos is not None:
                self.texto(tela, f'{segundos}s', (228, 140), 'pequena')

    def dialogo(self, tela, mensagem, titulo=None, topo=None, exibir_autor=True):
        autor, separador, fala = mensagem.partition(':')
        if not separador:
            autor, fala = titulo or 'INSCRIÇÃO', mensagem
        linhas = self.linhas(fala.strip(), tela.get_width()-272, 'fala')
        altura = (44 if exibir_autor else 20) + 35*len(linhas)
        y = tela.get_height()-altura-20 if topo is None else topo
        rect = pygame.Rect(120, y, tela.get_width()-240, altura)
        if exibir_autor:
            nome = self.renderizar(autor.upper(), 'pequena')
            tela.blit(nome, nome.get_rect(midtop=(rect.centerx, rect.y+10)))
        for i, linha in enumerate(linhas):
            imagem = self.renderizar(linha, 'fala')
            tela.blit(imagem, imagem.get_rect(midtop=(rect.centerx, rect.y+(35 if exibir_autor else 8)+i*35)))

    def interacao(self, tela, objeto, aviso):
        imagem = self.renderizar(aviso)
        rect = pygame.Rect(objeto.right+12, objeto.centery-19, imagem.get_width()+24, 38)
        rect.clamp_ip(tela.get_rect().inflate(-24, -24))
        tela.blit(imagem, (rect.x+12, rect.y+10))

    def inscricao(self, tela, objeto, texto):
        linhas = ['LÁPIDE'] + self.linhas(texto, 300)
        imagens = [self.renderizar(linha, 'pequena' if i == 0 else 'corpo')
                   for i, linha in enumerate(linhas)]
        area = pygame.Rect(objeto.right+16, objeto.top-28,
                           max(img.get_width() for img in imagens), len(linhas)*26)
        area.clamp_ip(pygame.Rect(16, 180, tela.get_width()-32, tela.get_height()-310))
        for i, img in enumerate(imagens):
            tela.blit(img, img.get_rect(midtop=(area.centerx, area.y+i*26)))
