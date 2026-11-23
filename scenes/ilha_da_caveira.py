"""Terceira ilha: ruínas, Guardião e confronto com o Rei Necromante."""
from functools import lru_cache
import math
import random

import pygame

from asset_loader import carregar_imagem
from camera import Camera
from enemies.skeleton import Skeleton
from scenes.mar import desenhar_mar
from scenes.planta import contorno_irregular
from scenes.terreno import faixa_irregular

PREPARACAO_GOLPE_MS = 550
FIM_IMPACTO_GOLPE_MS = 750
DURACAO_GOLPE_MS = 1100
INTERVALO_GOLPES_MS = 2200
RECUPERACAO_GOLPE_MS = 1100

class IlhaDaCaveira:
    nome = 'Ilha da Caveira'
    tamanho = (2600, 6400)
    inicio = (1272, 6040)

    def __init__(self):
        self.costa = contorno_irregular(((1050,6100),(800,5800),(900,5500),
            (580,5100),(570,4500),(790,4050),(650,3700),(750,3150),
            (1020,2850),(1000,2400),(600,2100),(530,1300),(800,950),
            (900,400),(1300,250),(1700,400),(1800,950),(2070,1300),
            (2000,2100),(1600,2400),(1580,2850),(1850,3150),
            (1950,3700),(1800,4050),(2030,4500),(2020,5100),
            (1700,5500),(1800,5800),(1550,6100)), 25)
        self.cais = pygame.Rect(1190,5950,220,400)
        self.barco = pygame.Rect(1435,6000,125,330)
        self.cais_final = pygame.Rect(1220,70,160,390)
        self.barco_final = pygame.Rect(1410,70,115,230)
        self.embarque_final = pygame.Rect(1220,90,160,200)
        self.guardiao = pygame.Rect(1160,2520,108,172)
        self.pontos_guardas = ((1450,5350),(1060,5020),(1710,4740),
            (1110,4250),(1680,3950),(1140,3700),(1530,3470),(1440,3180))
        self.bau = pygame.Rect(1252,550,96,84)
        self.bau_aberto = False
        self.conversou = False
        self.boss_ativo = False
        self.boss_morto_em = None
        self.ultimo_golpe = -3000
        self.proxima_invocacao = 0
        self.recuperacao_ate = 0
        self.boss_movendo = False
        self.centro_arena = (1300, 1670)
        self.fase_movimento = 'aproximacao'
        self.fase_movimento_desde = 0
        self.acao = None
        self.inicio_acao = 0
        self.golpe_aplicado = False
        self.invocacoes = []
        self.invocacao_concluida = False
        self.surgimentos = {}
        self.dano_boss_ate = 0
        self.reiniciar_dialogos_boss()
        self.portao = pygame.Rect(650,920,1300,35)
        self.entrada_arena = pygame.Rect(850,2380,900,30)
        self.muros = [pygame.Rect(780,4750,480,55),pygame.Rect(1390,4450,420,55),
                      pygame.Rect(900,3500,380,55),pygame.Rect(1480,3290,250,55)]
        self.decoracoes = []
        for x,y in ((860,4900),(1010,4900),(1160,4900),(1560,4700),
                     (1700,4680),(1830,4700),(850,3650),(1030,3650),
                     (1430,3860),(1610,3860)):
            self.decoracoes.append(('tumulo-antigo-lapide.png',pygame.Rect(x,y,65,86)))
        for x,y in ((760,3400),(1760,3750),(820,5100),(1680,5000)):
            self.decoracoes.append(('tumulo-antigo-cruz.png',pygame.Rect(x,y,70,105)))
        for arquivo, x,y,w,h in (
            ('muro-destruido-reto.png',760,4630,500,175),
            ('muro-destruido-baixo.png',1370,4360,470,130),
            ('arco-pedra-arruinado.png',1000,2800,270,270),
            ('arco-pedra-desabado.png',1450,4000,250,220),
            ('tumulo-antigo-violado.png',1660,3460,150,115),
            ('entulho-alvenaria-compacto.png',790,4200,125,90),
            ('entulho-alvenaria-espalhado.png',1660,3100,160,90),
            ('muro-destruido-baixo.png',900,3400,380,155),
            ('muro-destruido-reto.png',1480,3180,250,165)):
            self.decoracoes.append((arquivo,pygame.Rect(x,y,w,h)))
        for x,y in ((720,1300),(1730,1300),(720,1900),(1730,1900),
                     (850,2300),(1630,2300),(950,720),(1550,720)):
            self.decoracoes.append(('coluna-quebrada-alta.png',pygame.Rect(x,y,85,190)))
        for n,(x,y) in enumerate(((850,5700),(1600,5650),(650,5050),(1850,5000),
            (650,4430),(1850,4300),(780,3970),(1750,3950),(700,3550),
            (1770,3250),(1010,2800),(1500,2770),(650,2000),(1860,1950),
            (700,1100),(1810,1100),(930,430),(1580,430))):
            nome=('arvore-morta-alta.png','arvore-morta-larga.png',
                  'arvore-morta-tronco-quebrado.png','arvore-morta-inclinada.png')[n%4]
            r=pygame.Rect(0,0,180,245);r.midbottom=(x,y)
            self.decoracoes.append((nome,r))
        self.fundo_decorado = []
        for n,(x,y) in enumerate(((1080,5620),(1590,5360),(820,4520),(1580,4150),
                                 (850,3300),(1450,3000),(1500,2470),(1110,1050))):
            nome=('ossada-inteira.png','ossada-parcial.png','ossada-pilha.png','ossada-costelas.png')[n%4]
            self.fundo_decorado.append((nome,pygame.Rect(x,y,110,85)))
        rng=random.Random(37)
        for n in range(45):
            x=rng.choice((760,920,1650,1800))+rng.randrange(-40,40)
            y=rng.randrange(1000,5700)
            nome=('arbusto-seco-arredondado.png','capim-morto-denso.png','capim-morto-rasteiro.png')[n%3]
            self.fundo_decorado.append((nome,pygame.Rect(x,y,65,55)))
        self.trilhas = [faixa_irregular(((1300,6100),(1300,5500),(1470,5210),
            (1350,4950),(1490,4640),(1260,4280),(1350,4000),(1260,3650),
            (1370,3300),(1300,2900),(1320,2500),(1300,2240)),110)]
        terreno=pygame.Surface(self.tamanho,pygame.SRCALPHA)
        pygame.draw.polygon(terreno,'white',self.costa)
        pygame.draw.rect(terreno,'white',self.cais)
        pygame.draw.rect(terreno,'white',self.cais_final)
        self.terra=pygame.mask.from_surface(terreno)
        self.fundo_decorado=[(n,r) for n,r in self.fundo_decorado if self.em_terra(r)]
        # A costa ganha rochas sem fechar o acesso ao cais.
        for i,(x,y) in enumerate(self.costa[::7]):
            if y>5800:continue
            r=pygame.Rect(x-34,y-38,68,65)
            self.decoracoes.append((('rocha-costeira-alta.png' if i%3==0
                                     else 'rocha-costeira-arredondada.png'),r))
        for x,y in ((1460,5890),(1160,5300),(1570,4140),(1395,2770),(1540,990)):
            r=pygame.Rect(0,0,80,90);r.midbottom=(x,y)
            self.decoracoes.append(('bandeira-pirata.png',r))
        self.organizar_visual()
        self.organizar_composicao()
        self.manchas_solo=[]
        for cor,rect in (((77,72,60),pygame.Rect(800,5380,1000,650)),
                         ((74,69,61),pygame.Rect(600,4350,1400,1050)),
                         ((58,65,59),pygame.Rect(650,3150,1300,1050)),
                         ((80,74,59),pygame.Rect(1000,2460,600,340)),
                         ((57,58,57),pygame.Rect(600,1030,1400,1330))):
            pontos=tuple((round(rect.centerx+math.cos(i*math.tau/32)*rect.width/2),
                          round(rect.centery+math.sin(i*math.tau/32)*rect.height/2))
                         for i in range(32))
            self.manchas_solo.append((cor,contorno_irregular(pontos,18)))
        self.textura=[]
        for _ in range(1400):
            x,y=rng.randrange(600,2000),rng.randrange(350,6100)
            if self.em_terra(pygame.Rect(x,y,4,3)):
                self.textura.append((x,y,rng.choice(((76,73,62),(53,54,48),(88,81,65)))))
        self.obstaculos=[]
        self.atualizar_obstaculos()
        self.inimigos=[]
        for i,(x,y) in enumerate(self.pontos_guardas):
            e=Skeleton(x-20,y-60,patrulha=[(x-90,y-30),(x+90,y-30)],altura_visual=120)
            e.area_combate=pygame.Rect(600, y-260,1400,520)
            self.inimigos.append(e)
        self.boss=Skeleton(1280,1540)
        self.boss.vida=self.boss.vida_maxima=18
        self.boss.speed=1.4
        self.boss.duracao_atordoamento=0
        self.boss.detected=1500
        self.boss.area_combate=pygame.Rect(650,1100,1300,1200)
        self.boss.patrulha=[self.boss.rect.center]
        self.inimigos.append(self.boss)
        self.frascos=[pygame.Rect(1550,5460,32,46),pygame.Rect(970,3090,32,46),
                      pygame.Rect(1450,2500,32,46)]

    @staticmethod
    @lru_cache(maxsize=160)
    def imagem_cenario(nome, tamanho, rotacao=0):
        original=carregar_imagem('objects/'+nome)
        if rotacao:original=pygame.transform.rotate(original,rotacao)
        limite=original.get_bounding_rect(min_alpha=128)
        visivel=original.subsurface(limite)
        escala=min(tamanho[0]/visivel.get_width(),tamanho[1]/visivel.get_height())
        escalar=pygame.transform.scale if nome=='bandeira-pirata.png' else pygame.transform.smoothscale
        image=escalar(visivel,(max(1,round(visivel.get_width()*escala)),
                              max(1,round(visivel.get_height()*escala))))
        quadro=pygame.Surface(tamanho,pygame.SRCALPHA)
        quadro.blit(image,image.get_rect(midbottom=(tamanho[0]//2,tamanho[1])))
        return quadro

    def organizar_visual(self):
        """Escalas visíveis: Kia tem 118 px; árvores e arquitetura devem dominá-la."""
        for i,(nome,r) in enumerate(self.decoracoes):
            base=r.midbottom
            limites=carregar_imagem('objects/'+nome).get_bounding_rect(min_alpha=128)
            altura=None
            if nome.startswith('arvore-'):
                altura=(280,260,210,275)[i%4]
            elif nome.startswith('coluna-'):altura=225
            elif nome.startswith('arco-'):altura=300
            elif nome=='tumulo-antigo-lapide.png':altura=76
            elif nome=='tumulo-antigo-cruz.png':altura=108
            elif nome=='tumulo-antigo-violado.png':altura=125
            elif nome.startswith('muro-'):altura=140 if 'reto' in nome else 92
            elif nome.startswith('entulho-'):altura=70 if 'compacto' in nome else 50
            elif nome.startswith('rocha-'):altura=(64,80,96)[i%3]
            elif nome=='bandeira-pirata.png':altura=90
            if altura:
                r.size=(round(limites.width*altura/limites.height),altura)
                r.midbottom=base
        for i,(nome,r) in enumerate(self.fundo_decorado):
            base=r.midbottom
            limite=carregar_imagem('objects/'+nome).get_bounding_rect(min_alpha=128)
            if nome.startswith('ossada-'):
                largura={'ossada-inteira.png':108, 'ossada-parcial.png':72,
                         'ossada-pilha.png':63, 'ossada-costelas.png':60}[nome]
                r.size=(largura,round(largura*limite.height/limite.width))
            else:
                altura=55+i%3*8 if nome.startswith('arbusto-') else 28+i%3*6
                r.size=(round(altura*limite.width/limite.height),altura)
            r.midbottom=base
        # A colisão usa a própria estrutura que aparece no cenário.
        self.muros=[pygame.Rect(r.x+6,r.bottom-28,r.width-12,28)
                    for nome,r in self.decoracoes if nome.startswith('muro-')]

    def em_terra(self, rect):
        w,h=self.tamanho
        return all(0<=x<w and 0<=y<h and self.terra.get_at((x,y))
                   for x,y in (rect.topleft,(rect.right-1,rect.top),
                               (rect.left,rect.bottom-1),(rect.right-1,rect.bottom-1)))

    @staticmethod
    def apoio_decoracao(nome, rect):
        if nome.startswith('arvore-'):
            largura, altura = round(rect.width * .66), round(rect.height * .18)
            return pygame.Rect(rect.centerx-largura//2, rect.bottom-altura, largura, altura)
        return rect.inflate(-8, -8)

    def organizar_composicao(self):
        """Distribui volumes legíveis, preservando passagens e clareiras dos atores."""
        caminho = pygame.Surface(self.tamanho, pygame.SRCALPHA)
        for poligono in self.trilhas:
            pygame.draw.polygon(caminho, 'white', poligono)
        pygame.draw.rect(caminho, 'white', pygame.Rect(1220,350,160,600))
        corredor = pygame.mask.from_surface(caminho)
        self.zonas_livres = [self.guardiao.inflate(160,120), self.bau.inflate(160,160),
            self.cais.inflate(50,100), self.cais_final.inflate(50,70),
            self.barco.inflate(70,70), self.barco_final.inflate(70,70),
            pygame.Rect(900,1150,800,1060)]
        self.zonas_livres += [pygame.Rect(x-145,y-165,290,195) for x,y in self.pontos_guardas]
        self.zonas_livres += [r.inflate(90,110) for r in
            (pygame.Rect(1550,5460,32,46),pygame.Rect(970,3090,32,46),pygame.Rect(1450,2500,32,46))]
        def prioridade(item):
            nome, r = item
            categoria = (0 if nome.startswith(('arco-', 'muro-', 'coluna-')) else
                         1 if nome.startswith('arvore-') else
                         2 if nome.startswith('tumulo-') else 3)
            return categoria, r.y, r.x
        ocupados = []
        for nome, rect in sorted(self.decoracoes, key=prioridade):
            origem = rect.copy()
            mascara_rect = pygame.mask.Mask(rect.size, fill=True)
            def livre(candidato):
                if not pygame.Rect((0,0),self.tamanho).contains(candidato):return False
                apoio = (self.apoio_decoracao(nome,candidato) if nome.startswith(('arvore-','rocha-'))
                         else pygame.Rect(candidato.x+4,candidato.bottom-28,candidato.width-8,28))
                if not self.em_terra(apoio.inflate(10,10)):return False
                if candidato.collidelist(self.zonas_livres)>=0:return False
                if candidato.inflate(28,28).collidelist(ocupados)>=0:return False
                # Arcos enquadram a passagem; suas colunas ficam nas laterais.
                if nome.startswith('arco-'):
                    largura=round(candidato.width*.24)
                    for x in (candidato.left+6,candidato.right-largura-6):
                        base=pygame.Rect(x,candidato.bottom-36,largura,36)
                        if corredor.overlap(pygame.mask.Mask(base.size,fill=True),base.topleft):return False
                elif corredor.overlap(mascara_rect,candidato.topleft):return False
                return True
            if not livre(rect):
                candidatos = ((round(math.cos(i*math.tau/32)*raio),
                               round(math.sin(i*math.tau/32)*raio))
                              for raio in range(24,1201,24) for i in range(32))
                for dx,dy in candidatos:
                    candidato=origem.move(dx,dy)
                    if livre(candidato):
                        rect.topleft=candidato.topleft
                        break
                else:raise ValueError(f'Sem espaço de composição para {nome}')
            ocupados.append(rect.copy())
        # Colisões acompanham os muros reposicionados.
        self.muros=[pygame.Rect(r.x+6,r.bottom-28,r.width-12,28)
                    for nome,r in self.decoracoes if nome.startswith('muro-')]
        self.fundo_decorado=[(n,r) for n,r in self.fundo_decorado
                            if self.em_terra(r) and r.collidelist(ocupados+self.zonas_livres)<0
                            and not corredor.overlap(pygame.mask.Mask(r.size,fill=True),r.topleft)]

    def atualizar_obstaculos(self):
        self.obstaculos=[('muro',r) for r in self.muros]
        self.obstaculos.extend([('guardiao',pygame.Rect(self.guardiao.centerx-22,
            self.guardiao.bottom-28,44,28)),('bau',self.bau),('barco',self.barco),
            ('barco',self.barco_final)])
        for nome,r in self.decoracoes:
            if nome.startswith('arco-'):
                largura=round(r.width*.24)
                self.obstaculos.extend(('coluna',pygame.Rect(x,r.bottom-36,largura,36))
                                      for x in (r.left+6,r.right-largura-6))
            elif nome.startswith('arvore-'):
                self.obstaculos.append(('arvore',pygame.Rect(r.centerx-15,r.bottom-22,30,22)))
            elif nome=='bandeira-pirata.png':
                self.obstaculos.append(('mastro',pygame.Rect(r.right-13,r.bottom-10,8,10)))
            elif not nome.startswith('muro-'):
                self.obstaculos.append(('estrutura',pygame.Rect(r.x+8,r.bottom-28,r.width-16,28)))
        if self.boss_morto_em is None:self.obstaculos.append(('portao',self.portao))
        if not self.conversou or (self.boss_ativo and self.boss.vivo):
            self.obstaculos.append(('portao',self.entrada_arena))

    def objetivo(self,j):
        if j.metade_mapa2:return 'Embarque no bote'
        if j.tem_chave[0]:return 'Abra o baú final'
        if j.chaves[0] is not None:return 'Pegue a chave do Necromante'
        if self.boss_morto_em is not None:return 'Pegue a chave do Necromante'
        if self.boss_ativo:return 'Derrote o Rei Necromante'
        if not self.conversou:return 'Fale com o Guardião da Luz'
        return 'Enfrente o Rei Necromante'

    def interacao(self,j):
        if j.metade_mapa2 and j.perto(self.embarque_final,35):
            return 'barco_final',None,'[E] Embarcar para a próxima ilha'
        if j.chaves[0] is not None and j.perto(j.chaves[0]):return 'chave',0,'[E] Pegar chave'
        for i,r in enumerate(j.frascos):
            if j.perto(r) and j.kia.vida<j.vida_maxima:return 'frasco',i,j.aviso_frasco()
        if j.perto(self.guardiao,90):return 'guardiao',None,'[E] Conversar'
        if not self.bau_aberto and j.perto(self.bau,60):return 'bau_final',None,'[E] Abrir baú final'
        return None

    def interagir(self,j):
        alvo=self.interacao(j)
        if alvo is None or j.esquivando():return
        tipo,i,_=alvo
        if tipo!='guardiao':j.kia.iniciar_interacao()
        if tipo=='barco_final':
            j.estado='partida_final';j.inicio_partida_final=pygame.time.get_ticks()
            j.ataque_r=None
        elif tipo=='guardiao':
            j.abrir_dialogo_guardiao()
        elif tipo=='frasco' and j.kia.vida<j.vida_maxima:
            j.kia.vida=min(j.vida_maxima,j.kia.vida+3);j.frascos.pop(i);j.som('coleta')
        elif tipo=='chave':
            j.chaves[0]=None;j.tem_chave[0]=True;j.som('vitoria_chave');j.falar('Chave do baú final adquirida.')
        elif tipo=='bau_final':
            if self.boss.vivo or not j.tem_chave[0]:
                j.falar('Kia: Preciso da chave que o Necromante guarda.')
            else:
                j.tem_chave[0]=False;self.bau_aberto=True;j.metade_mapa2=True
                j.som('bau')
                j.abrir_mapa_tesouro(pygame.time.get_ticks())

    def configurar_inimigo(self,e,j):
        e.vida_maxima=e.vida
        e.obter_obstaculos=j.obstaculos_movimento
        e.em_terra=self.em_terra
        e.ao_som=(None if e is self.boss else
                  lambda nome,ator=e: j.audio.tocar_inimigo(nome,ator,j.kia))

    def atualizar(self,j,now):
        anterior=j.kia.x,j.kia.y
        if j.esquiva_atualizada<j.esquiva_ate:j.mover_esquiva(now)
        else:j.kia.move(j.obstaculos_kia(),*self.tamanho)
        if not self.em_terra(j.kia.rect):j.posicionar_kia(*anterior)
        j.camera.update(j.kia.bodyRect)
        if self.conversou and not self.boss_ativo and j.kia.rect.centery<2310:
            self.boss_ativo=True;self.proxima_invocacao=now+8000;self.atualizar_obstaculos()
            self.fase_movimento='aproximacao';self.fase_movimento_desde=now
            self.reiniciar_dialogos_boss()
            j.falar('Rei Necromante: Estava esperando por você! HAHAHAHA', legenda=True)
            self.vocalizar_boss(j,'rei_risada',now)
            self.proxima_fala_boss=j.mensagem_ate+1200
            self.enfileirar_dialogo_boss('entrada',('Kia: Então vamos acabar com essa espera.',))
        if j.ataque_r is not None:
            if now-j.inicio_ataque>=180:j.ataque_r=None
            elif j.kia.ataque_ativo(now):
                for e in self.inimigos:
                    if (not e.vivo or e in j.atingidos or e in self.surgimentos
                            or (e is self.boss and not self.boss_ativo)):continue
                    alvo=e.rect.inflate(30,60) if e is self.boss else e.rect
                    if not j.ataque_r.colliderect(alvo):continue
                    e.recebeDano(.5 if e is self.boss else 1)
                    j.atingidos.add(e)
                    if e is self.boss:j.som('rei_dano' if e.vivo else 'rei_derrota')
                    elif not e.vivo:j.som('morte')
                    if e is self.boss:self.dano_boss_ate=now+80
                    if not e.vivo:
                        if e is self.boss:
                            self.boss_morto_em=now;self.acao=None
                            self.fila_dialogos_boss.clear()
                            for outro in self.inimigos:
                                if getattr(outro,'invocado',False):outro.vivo=False
                            self.invocacoes.clear();self.atualizar_obstaculos()
                        else:
                            j.skeletons_derrotados+=1
                            if j.skeletons_derrotados%3==0:
                                r=pygame.Rect(0,0,32,46);j.posicionar_drop(r,e.rect.center);j.frascos.append(r)
        if self.boss_morto_em is not None and now-self.boss_morto_em>=1500 and not j.chaves_dropadas[0]:
            r=pygame.Rect(0,0,40,42);j.posicionar_drop(r,self.boss.rect.center)
            j.chaves[0]=r;j.chaves_dropadas[0]=True
            j.falar('Kia: Consegui derrotar esse maldito! Essa deve ser a chave para o tesouro...')
        for e in list(self.inimigos):
            if not e.vivo or e is self.boss or not j.kia.viva:continue
            if e in self.surgimentos:
                if now-self.surgimentos[e]<900:continue
                del self.surgimentos[e]
            old=e.rect.copy()
            perseguindo = (getattr(e,'invocado',False)
                           or e.area_combate.collidepoint(j.kia.rect.center))
            if (getattr(e,'invocado',False) and e.caminho_desvio
                    and pygame.Vector2(e.caminho_desvio[-1]).distance_to(j.kia.bodyRect.center)>96
                    and now-e.tentativa_desvio>=500):
                e.caminho_desvio.clear()
            if e.caminho_desvio:e.seguir_desvio(j.kia,self.inimigos)
            elif perseguindo:e.seguir(j.kia,self.inimigos)
            else:e.patrulhar(j.kia,self.inimigos)
            feet=pygame.Rect(e.rect.x+5,e.rect.bottom-12,30,12)
            if not self.em_terra(feet):e.rect=old
            if e.rect==old and not e.caminho_desvio:
                alvo=(j.kia.bodyRect.center if perseguindo
                      else e.patrulha[e.ponto_pat])
                e.planejar_desvio(alvo)
            vida=j.kia.vida
            e.atacar(j.kia,pode_atingir=(not j.esquivando() and now-j.ultimo_dano>=600))
            if j.kia.vida<vida:j.ultimo_dano=now;j.som('dano')
        self.atualizar_boss(j,now)

    def reiniciar_dialogos_boss(self):
        self.dialogos_boss_vistos=set()
        self.fila_dialogos_boss=[]
        self.proxima_fala_boss=0
        self.proxima_voz_boss=0
        self.golpes_com_voz=0

    def vocalizar_boss(self,j,nome,now):
        if now<self.proxima_voz_boss:return False
        j.som(nome)
        self.proxima_voz_boss=now+(4000 if nome=='rei_risada' else 2800)
        return True

    def enfileirar_dialogo_boss(self,evento,falas):
        if evento not in self.dialogos_boss_vistos:
            self.dialogos_boss_vistos.add(evento)
            self.fila_dialogos_boss.extend(falas)

    def atualizar_dialogos_boss(self,j,now):
        fracao=self.boss.vida/self.boss.vida_maxima
        if fracao<=.5:
            self.enfileirar_dialogo_boss('metade_vida',(
                'Rei Necromante: Insolente! Este reino ainda me pertence!',
                'Kia: Seus mortos não vão salvar você.',))
        if fracao<=.25:
            self.enfileirar_dialogo_boss('ultima_resistencia',(
                'Rei Necromante: Eu... não posso morrer!',
                'Kia: Toda maldição tem um fim.',))
        # Uma legenda por vez, com respiro entre falas e sem interromper avisos.
        if (self.fila_dialogos_boss and now>=self.proxima_fala_boss
                and now>=j.mensagem_ate):
            j.falar(self.fila_dialogos_boss.pop(0),legenda=True)
            self.proxima_fala_boss=j.mensagem_ate+1200

    def atualizar_boss(self,j,now):
        self.boss_movendo = False
        if not self.boss_ativo or not self.boss.vivo or not j.kia.viva:return
        self.atualizar_dialogos_boss(j,now)
        b=self.boss
        if self.acao=='invocacao':
            if now-self.inicio_acao>=700 and not self.invocacao_concluida:
                self.invocacao_concluida=True
                j.som('surgimento')
                for pos in self.invocacoes:
                    e=Skeleton(pos[0]-20,pos[1]-60,altura_visual=120)
                    e.invocado=True;e.area_combate=b.area_combate;e.patrulha=[e.rect.center]
                    e.detected=float('inf')
                    self.configurar_inimigo(e,j);self.inimigos.append(e);self.surgimentos[e]=now
            if now-self.inicio_acao>=1700:
                self.acao=None;self.invocacoes.clear()
                self.proxima_invocacao=now+18000
                self.recuperacao_ate=now+1200
                self.fase_movimento='centro';self.fase_movimento_desde=now
                b.caminho_desvio.clear()
            return
        if self.acao=='ataque':
            elapsed=now-self.inicio_acao
            if elapsed>=PREPARACAO_GOLPE_MS and not self.golpe_aplicado:
                self.golpe_aplicado=True
                j.som('rei_impacto')
                if (not j.esquivando() and now-j.ultimo_dano>=600
                        and self.area_golpe.colliderect(j.kia.bodyRect)):
                    j.kia.recebeDano();j.ultimo_dano=now;j.som('dano')
            if elapsed>=DURACAO_GOLPE_MS:
                self.acao=None
                self.recuperacao_ate=now+RECUPERACAO_GOLPE_MS
                self.fase_movimento='pausa';self.fase_movimento_desde=now
                b.caminho_desvio.clear()
            return
        if now < self.recuperacao_ate:return
        # As pausas são janelas seguras para contra-atacar, mesmo perto do rei.
        pausa_ms={'pausa':1000,'pausa_centro':1500}.get(self.fase_movimento,0)
        if now-self.fase_movimento_desde<pausa_ms:return
        distancia=pygame.Vector2(b.rect.center).distance_to(j.kia.bodyRect.center)
        if distancia<130 and now-self.ultimo_golpe>=INTERVALO_GOLPES_MS:
            self.iniciar_golpe(j,now)
            return
        if self.fase_movimento=='aproximacao' and now-self.fase_movimento_desde>=2200:
            self.fase_movimento='pausa';self.fase_movimento_desde=now
            b.caminho_desvio.clear()
            return
        if self.fase_movimento=='pausa':
            self.fase_movimento='centro';self.fase_movimento_desde=now
        if self.fase_movimento=='centro':
            if (pygame.Vector2(b.rect.center).distance_to(self.centro_arena)<=30
                    or now-self.fase_movimento_desde>=4000):
                self.fase_movimento='pausa_centro';self.fase_movimento_desde=now
                self.vocalizar_boss(j,'rei_risada',now)
                b.caminho_desvio.clear()
                return
            anterior=b.rect.copy()
            if b.caminho_desvio:b.seguir_desvio(j.kia,self.inimigos)
            else:
                b.patrulha=[self.centro_arena];b.ponto_pat=0
                b.patrulhar(j.kia,self.inimigos)
                if b.rect==anterior:b.planejar_desvio(self.centro_arena)
            self.boss_movendo=b.rect!=anterior
            return
        if self.fase_movimento=='pausa_centro':
            self.fase_movimento='aproximacao';self.fase_movimento_desde=now
        distancia=pygame.Vector2(b.rect.center).distance_to(j.kia.bodyRect.center)
        vivos=sum(e.vivo and getattr(e,'invocado',False) for e in self.inimigos)
        if now>=self.proxima_invocacao and vivos==0 and distancia>=115:
            self.inicio_acao=now;self.acao='invocacao'
            j.som('rei_invocacao')
            self.vocalizar_boss(j,'rei_risada',now)
            self.enfileirar_dialogo_boss('primeira_invocacao',(
                'Rei Necromante: Levantem-se! Tragam-me a alma dela!',
                'Kia: Você não consegue lutar sozinho?',))
            self.invocacao_concluida=False;self.invocacoes=[]
            for pos in ((1030,1480),(1550,1800)):
                r=pygame.Rect(0,0,44,110);j.posicionar_drop(r,pos)
                self.invocacoes.append(r.midbottom)
            return
        if distancia>=75:
            anterior=b.rect.copy()
            if b.caminho_desvio:b.seguir_desvio(j.kia,self.inimigos)
            else:
                old=b.rect.copy();b.seguir(j.kia,self.inimigos)
                if b.rect==old:b.planejar_desvio(j.kia.bodyRect.center)
            self.boss_movendo = b.rect != anterior

    def iniciar_golpe(self,j,now):
        j.som('rei_preparacao')
        voz='rei_urro' if self.golpes_com_voz%2==0 else 'rei_grito'
        if self.vocalizar_boss(j,voz,now):self.golpes_com_voz+=1
        self.ultimo_golpe=now
        self.inicio_acao=now
        self.acao='ataque'
        self.golpe_aplicado=False
        self.boss.caminho_desvio.clear()
        dx=j.kia.bodyRect.centerx-self.boss.rect.centerx
        dy=j.kia.bodyRect.centery-self.boss.rect.centery
        self.boss.atualizar_direcao(dx,dy)
        self.area_golpe=self.boss.rect.inflate(130,120)

    @lru_cache(maxsize=32)
    def bloco(self,coluna,linha):
        s=pygame.Surface((512,512),pygame.SRCALPHA)
        c=Camera(512,512,*self.tamanho);c.x=coluna*512;c.y=linha*512
        pygame.draw.polygon(s,(92,85,72),[c.pos(*p) for p in self.costa])
        interior=[pygame.Vector2(p).lerp((1300,3200),.024) for p in self.costa]
        solo=pygame.Surface((512,512),pygame.SRCALPHA)
        solo.fill((66,65,57))
        for cor,pontos in self.manchas_solo:
            pygame.draw.polygon(solo,cor,[c.pos(*p) for p in pontos])
        mascara=pygame.Surface((512,512),pygame.SRCALPHA)
        pygame.draw.polygon(mascara,'white',[c.pos(*p) for p in interior])
        solo.blit(mascara,(0,0),special_flags=pygame.BLEND_RGBA_MIN)
        s.blit(solo,(0,0))
        for x,y,cor in self.textura:
            if c.x<=x<c.x+512 and c.y<=y<c.y+512:
                pygame.draw.line(s,cor,c.pos(x,y),c.pos(x+3,y),1)
        for poly in self.trilhas:pygame.draw.polygon(s,(104,93,73),[c.pos(*p) for p in poly])
        for nome,r in self.fundo_decorado:
            if c.rect(r).colliderect(s.get_rect()):s.blit(self.imagem_cenario(nome,r.size),c.rect(r))
        for x,y in ((1080,4750),(1420,4200),(1040,3400),(1200,2630)):
            r=pygame.Rect(x,y,240,200)
            if c.rect(r).colliderect(s.get_rect()):s.blit(self.imagem_cenario('piso-antigo-lajes.png',r.size),c.rect(r))
        ritual=pygame.Rect(850,1150,900,1050)
        if c.rect(ritual).colliderect(s.get_rect()):s.blit(self.imagem_cenario('piso-ritual-arena.png',ritual.size),c.rect(ritual))
        for cais in (self.cais,self.cais_final):
            pygame.draw.rect(s,(84,60,40),c.rect(cais))
            for y in range(cais.top,cais.bottom,25):
                falha=(y//25)%7
                largura=cais.width-8-(12 if falha==3 else 0)
                pygame.draw.rect(s,(127+falha*2,96+falha,62),c.rect(pygame.Rect(cais.x+4,y,largura,20)))
                pygame.draw.line(s,(67,47,31),c.pos(cais.x+75,y),c.pos(cais.x+78,y+19),2)
        return s

    def imagem_boss(self,now):
        direcao={'baixo':'frente','cima':'costas','esquerda':'esquerda','direita':'direita'}[self.boss.direcao]
        if self.boss_morto_em is not None:
            nome=f'derrota-{min(6,1+(now-self.boss_morto_em)//250):02}.png'
        elif self.acao=='invocacao':
            fase=('preparacao','conjurando','finalizacao')[min(2,(now-self.inicio_acao)//570)]
            nome=f'invocacao-{fase}-{direcao}.png'
        elif self.acao=='ataque':
            fase=('preparacao' if now-self.inicio_acao<PREPARACAO_GOLPE_MS else
                  'golpe' if now-self.inicio_acao<FIM_IMPACTO_GOLPE_MS else 'recuperacao')
            nome=f'{fase}-{direcao}.png'
        elif now<self.dano_boss_ate:nome=f'dano-impacto-{direcao}.png'
        else:nome=f'andar-{1+now//180%3:02}-{direcao}.png' if self.boss_movendo else f'parado-{direcao}.png'
        return carregar_imagem('enemies/rei-necromante/'+nome,(260,260))

    def desenhar(self,j):
        s,c=j.screen,j.camera;now=pygame.time.get_ticks();desenhar_mar(s,c)
        for y in range(max(0,c.y//512),min(12,(c.y+s.get_height())//512)+1):
            for x in range(max(0,c.x//512),min(5,(c.x+s.get_width())//512)+1):
                s.blit(self.bloco(x,y),c.pos(x*512,y*512))
        camadas=[]
        for nome,r in self.decoracoes:
            camadas.append((r.bottom,self.imagem_cenario(nome,r.size),r.topleft))
        for nome,r in (('guardiao-da-luz.png',self.guardiao),('bote.png',self.barco),
                       ('bote.png',self.barco_final),
                       ('bau-final-fechado.png',self.bau)):
            camadas.append((r.bottom,self.imagem_cenario(nome,r.size,90 if nome=='bote.png' else 0),r.topleft))
        for portao in (self.portao,self.entrada_arena):
            if any(n=='portao' and r is portao for n,r in self.obstaculos):
                pontos=[(x,portao.centery) for x in range(portao.left,portao.right,12)
                        if self.em_terra(pygame.Rect(x,portao.centery,1,1))]
                if pontos:
                    pygame.draw.line(s,(68,119,123),c.pos(*pontos[0]),c.pos(*pontos[-1]),2)
                    for x,y in pontos[::3]:
                        altura=5+round(3*math.sin(now/350+x))
                        pygame.draw.line(s,(90,158,163),c.pos(x,y),c.pos(x,y-altura),1)
        for pos in self.invocacoes:
            frame=1+min(8,(now-self.inicio_acao)//180)
            image=carregar_imagem(f'effects/circulo-invocacao-{frame:02}.png',(130,110))
            s.blit(image,c.rect(image.get_rect(center=pos)))
        for e in self.inimigos:
            if e is self.boss:
                if not e.vivo and self.boss_morto_em is None:continue
                image=self.imagem_boss(now);pos=(e.rect.centerx-130,e.rect.bottom-245)
            elif not e.vivo and not e.em_derrota():continue
            elif e in self.surgimentos:
                frame=min(6,1+(now-self.surgimentos[e])//150)
                image=carregar_imagem(f'effects/aparicao-skeleton-{frame:02}.png',(140,160))
                pos=(e.rect.centerx-70,e.rect.bottom-150)
            else:
                image,anchor=e.visual();pos=(e.rect.centerx-anchor,e.rect.bottom-image.get_height())
            camadas.append((e.rect.bottom,image,pos))
        image,pos=j.kia.visual(j.ataque_r is not None)
        camadas.append((j.kia.rect.bottom,image,pos))
        for r in j.frascos:camadas.append((r.bottom,carregar_imagem('objects/frasco.png',r.size),r.topleft))
        if j.chaves[0] is not None:
            r=j.chaves[0];camadas.append((r.bottom,carregar_imagem('objects/chave-bau-final.png',r.size),r.topleft))
        for _,image,pos in sorted(camadas,key=lambda t:t[0]):
            destino=c.rect(image.get_rect(topleft=pos))
            if s.get_rect().colliderect(destino):s.blit(image,destino)
        fala_boss_y=None
        if self.boss_ativo and self.boss.vivo:
            barra=pygame.Rect(0,151,480,12)
            barra.centerx=s.get_width()//2
            nome='Rei Necromante'
            j.texto(nome,(barra.centerx-j.font.size(nome)[0]//2,125))
            pygame.draw.rect(s,(45,30,35),barra)
            preenchida=barra.copy()
            preenchida.width=round(barra.width*self.boss.vida/self.boss.vida_maxima)
            pygame.draw.rect(s,(149,45,63),preenchida)
            fala_boss_y=barra.bottom+12
            if self.acao=='ataque' and now-self.inicio_acao<PREPARACAO_GOLPE_MS:
                pygame.draw.ellipse(s,(193,103,60),c.rect(self.area_golpe),2)
        for e in self.inimigos:
            if e.vivo and e is not self.boss:
                r=c.rect(e.rect)
                pygame.draw.rect(s,(150,55,55),(r.x,r.bottom-e.sprite_altura-10,r.width*e.vida/e.vida_maxima,4))
        j.desenhar_hud(self.objetivo(j),fala_boss_y=fala_boss_y)
        alvo=self.interacao(j)
        if alvo and j.kia.viva and not j.esquivando():
            tipo,i,aviso=alvo
            rect={'guardiao':self.guardiao,'bau_final':self.bau,
                  'barco_final':self.embarque_final}.get(tipo)
            if tipo=='frasco':rect=j.frascos[i]
            if tipo=='chave':rect=j.chaves[0]
            j.desenhar_aviso_interacao(rect,aviso)
