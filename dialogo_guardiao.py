"""Janela de narrativa do Guardião; texto editável separado da interface."""
import json
import math
import pygame
from asset_loader import ASSETS, carregar_imagem
from menu_principal import MenuPrincipal


class DialogoGuardiao(MenuPrincipal):
    opcoes = ('Anterior','Continuar')
    acoes = ('anterior','avancar')

    def __init__(self, tamanho):
        super().__init__(tamanho, '', '')
        dados=json.loads((ASSETS/'narrativa/guardiao.json').read_text(encoding='utf-8'))
        self.nome=dados['personagem']
        self.paginas=dados['paginas']
        self.pagina=0
        self.selecionado=1
        self.cena=None
        self.painel=pygame.Rect(80,55,tamanho[0]-160,tamanho[1]-110)
        self.botoes=[pygame.Rect(500,540,240,54),pygame.Rect(815,540,240,54)]
        self.fonte=pygame.font.SysFont('georgia',25,bold=True)
        self.fonte_titulo=pygame.font.SysFont('georgia',37,bold=True)
        self.fonte_capitulo=pygame.font.SysFont('georgia',27,bold=True)
        self.fonte_corpo=pygame.font.SysFont('georgia',24)
        self.fonte_indice=pygame.font.SysFont('georgia',18)
        original=carregar_imagem('objects/guardiao-da-luz.png')
        b=original.get_bounding_rect(min_alpha=128)
        busto=original.subsurface((b.x,b.y,b.width,round(b.height*.68)))
        fator=min(260/busto.get_width(),340/busto.get_height())
        self.retrato=pygame.transform.smoothscale(busto,(round(busto.get_width()*fator),round(busto.get_height()*fator)))
        self.veu=pygame.Surface(tamanho,pygame.SRCALPHA)
        self.veu.fill((3,11,16,205))
        self.inicio_luz=pygame.time.get_ticks()
        self.aura=pygame.transform.smoothscale(self.criar_halo(140,(246,209,126),95),(280,360))
        self.luz_lanterna=self.criar_halo(64,(255,220,137),115)
        self.luz_amuleto=self.criar_halo(40,(255,242,183),100)
        self.particulas=pygame.Surface((284,363),pygame.SRCALPHA)

    @staticmethod
    def criar_halo(raio,cor,alpha):
        luz=pygame.Surface((raio*2,raio*2),pygame.SRCALPHA)
        for r in range(raio,0,-1):
            intensidade=round(alpha*(1-r/raio)**2)
            pygame.draw.circle(luz,(*cor,intensidade),(raio,raio),r)
        return luz

    def desenhar_guardiao(self,tela,moldura):
        tempo=max(0,pygame.time.get_ticks()-self.inicio_luz)/1000
        entrada=min(1,tempo/.65)
        pulso=.90+.10*math.sin(tempo*1.7)
        clip=tela.get_clip()
        tela.set_clip(clip.clip(moldura.inflate(-4,-4)))
        self.aura.set_alpha(round(190*entrada*pulso))
        tela.blit(self.aura,self.aura.get_rect(center=moldura.center))
        retrato=self.retrato.get_rect(center=moldura.center)
        tela.blit(self.retrato,retrato)
        for luz,x,y in ((self.luz_lanterna,.05,.26),(self.luz_amuleto,.50,.58)):
            luz.set_alpha(round(190*entrada*pulso))
            centro=(round(retrato.x+retrato.width*x),round(retrato.y+retrato.height*y))
            tela.blit(luz,luz.get_rect(center=centro))
        self.particulas.fill((0,0,0,0))
        for n in range(16):
            progresso=(n*.381966+tempo*(.07+(n%3)*.012))%1
            x=24+(n*73)%236+round(5*math.sin(tempo+n))
            y=round(350-progresso*330)
            alpha=round(170*entrada*math.sin(math.pi*progresso))
            cor=(255,234,167,alpha)
            pygame.draw.circle(self.particulas,cor,(x,y),1+n%2)
            if n%4==0:
                pygame.draw.line(self.particulas,cor,(x-3,y),(x+3,y))
                pygame.draw.line(self.particulas,cor,(x,y-3),(x,y+3))
        tela.blit(self.particulas,moldura)
        tela.set_clip(clip)

    def iniciar(self, cena):
        self.cena=cena.copy()
        self.pagina=0
        self.selecionado=1
        self.inicio_luz=pygame.time.get_ticks()

    def avancar(self):
        if self.pagina==len(self.paginas)-1:return 'concluir'
        self.pagina+=1
        self.selecionado=1
        return None

    def evento(self, evento):
        if evento.type==pygame.KEYDOWN:
            if evento.key==pygame.K_ESCAPE:return 'fechar'
            if evento.key==pygame.K_RIGHT:return self.avancar()
            if evento.key==pygame.K_LEFT:
                self.pagina=max(0,self.pagina-1)
                return None
        acao=super().evento(evento)
        if self.pagina==0 and self.selecionado==0:self.selecionado=1
        if acao=='anterior':self.pagina=max(0,self.pagina-1)
        elif acao=='avancar':return self.avancar()
        return None

    def linhas(self,texto,largura):
        linhas=[]
        for paragrafo in texto.split('\n\n'):
            if linhas:linhas.append('')
            linha=''
            for palavra in paragrafo.split():
                nova=(linha+' '+palavra).strip()
                if linha and self.fonte_corpo.size(nova)[0]>largura:
                    linhas.append(linha);linha=palavra
                else:linha=nova
            if linha:linhas.append(linha)
        return linhas

    def desenhar(self,tela):
        if self.cena is not None:tela.blit(self.cena,(0,0))
        else:tela.fill((10,24,32))
        tela.blit(self.veu,(0,0))
        pygame.draw.rect(tela,(17,32,38),self.painel,border_radius=14)
        pygame.draw.rect(tela,(166,133,78),self.painel,2,border_radius=14)
        titulo=self.fonte_titulo.render(self.nome,True,(235,205,146))
        tela.blit(titulo,titulo.get_rect(midtop=(self.tamanho[0]//2,80)))
        pygame.draw.line(tela,(107,91,62),(115,135),(self.tamanho[0]-115,135),1)
        moldura=pygame.Rect(120,158,284,363)
        pygame.draw.rect(tela,(24,43,46),moldura,border_radius=8)
        pygame.draw.rect(tela,(103,88,58),moldura,1,border_radius=8)
        self.desenhar_guardiao(tela,moldura)
        pagina=self.paginas[self.pagina]
        capitulo=self.fonte_capitulo.render(pagina['titulo'],True,(225,196,140))
        tela.blit(capitulo,(450,164))
        for i,linha in enumerate(self.linhas(pagina['texto'],665)):
            tela.blit(self.fonte_corpo.render(linha,True,(245,243,232)),(450,218+i*32))
        indice=self.fonte_indice.render(f'{self.pagina+1} / {len(self.paginas)}',True,(196,184,156))
        tela.blit(indice,indice.get_rect(center=(261,550)))
        self.opcoes=('Anterior','Concluir' if self.pagina==len(self.paginas)-1 else 'Continuar')
        self.desenhar_botoes(tela)
        dica=self.fonte_indice.render('Setas esquerda/direita: páginas    Enter ou clique: avançar    Esc: fechar',True,(229,223,205))
        tela.blit(dica,dica.get_rect(center=(self.tamanho[0]//2,self.tamanho[1]-26)))
