"""Áudio por contexto, com música em streaming e canais separados para ambientes."""
from functools import lru_cache
import json
import logging
import math
import random

import pygame
from asset_loader import ASSETS


@lru_cache(maxsize=96)
def carregar_som(caminho,formato):
    return pygame.mixer.Sound(caminho)


class AudioJogo:
    def __init__(self):
        self.pasta=ASSETS/'audio'
        self.catalogo=json.loads((self.pasta/'catalogo.json').read_text(encoding='utf-8'))
        self.habilitado=pygame.mixer.get_init() is not None
        self.erros=[]
        self.sons={}
        self.ultimos={}
        self.variantes={}
        self.loops={}
        self.volumes_loops={}
        self.ambientes_intermitentes={}
        self.sorteio_ambiente=random.Random()
        self.master=.8
        self.musica_atual=None
        self.musica_alvo=None
        self.inicio_troca=0
        self.volume_musica=0
        self.volume_saida=0
        self.estado_anterior=None
        self.ilha_anterior=None
        self.viva_anterior=True
        self.ultima_posicao=None
        self.proximo_passo_kia=0
        self.proxima_remada=0
        self.proximo_macaco=0
        self.proxima_gaivota=0
        self.chamadas_gaivota=0
        self.mapa_revelado=False
        self.ultima_mare=None
        self.proximo_ambiente=0
        self.volume_mar=1
        if self.habilitado:
            pygame.mixer.set_num_channels(max(24,pygame.mixer.get_num_channels()))
            pygame.mixer.set_reserved(10)

    def _som(self,arquivo):
        if arquivo not in self.sons:
            try:
                self.sons[arquivo]=carregar_som(str(self.pasta/arquivo),pygame.mixer.get_init())
            except (pygame.error,OSError) as erro:
                self.erros.append((arquivo,str(erro)))
                logging.warning('Falha de áudio %s: %s',arquivo,erro)
                self.sons[arquivo]=None
        return self.sons[arquivo]

    def tocar(self,nome,agora=None,volume=1):
        if not self.habilitado or not pygame.mixer.get_init():return
        info=self.catalogo['efeitos'].get(nome)
        if not info:return
        agora=pygame.time.get_ticks() if agora is None else agora
        if agora-self.ultimos.get(nome,-1000000)<info['intervalo_ms']:return
        indice=self.variantes.get(nome,0)%len(info['arquivos'])
        som=self._som(info['arquivos'][indice])
        if som is None:return
        if nome.startswith('passo_'):canal=pygame.mixer.Channel(4)
        elif nome.startswith('menu_'):canal=pygame.mixer.Channel(5)
        # Uma única voz da Kia por vez, mesmo ao atacar e esquivar rapidamente.
        elif nome.startswith('kia_') or nome=='dano':canal=pygame.mixer.Channel(8)
        elif nome in ('rei_risada','rei_urro','rei_grito','rei_dano','rei_derrota'):
            canal=pygame.mixer.Channel(9)
        else:
            canal=next((pygame.mixer.Channel(i) for i in range(10,24)
                        if not pygame.mixer.Channel(i).get_busy()),None)
        if canal is None:return
        self.ultimos[nome]=agora
        self.variantes[nome]=indice+1
        canal.set_volume(self.master*info['volume']*max(0,min(1,volume)))
        canal.play(som)

    def _loop(self,canal_id,nome,volume=1):
        canal=pygame.mixer.Channel(canal_id)
        if nome is None or volume<=.001:
            if self.loops.get(canal_id) is not None:canal.fadeout(350)
            self.loops[canal_id]=None
            return
        info=self.catalogo['ambientes'][nome]
        iniciou=self.loops.get(canal_id)!=nome or not canal.get_busy()
        if iniciou:
            som=self._som(info['arquivo'])
            if som is None:return
            canal.play(som,loops=-1,fade_ms=650)
            self.loops[canal_id]=nome
        volume_final=self.master*info['volume']*max(0,min(1,volume))
        if iniciou or self.volumes_loops.get(canal_id)!=volume_final:
            canal.set_volume(volume_final)
            self.volumes_loops[canal_id]=volume_final

    def tocar_inimigo(self,nome,inimigo,ouvinte):
        distancia=math.dist(inimigo.rect.center,ouvinte.bodyRect.center)
        if distancia<650:
            self.tocar(nome,volume=(1-distancia/650)**1.2)

    def _ambiente_intermitente(self,canal_id,nome,agora,pausa_min=6000,pausa_max=14000):
        if nome is None:
            if self.ambientes_intermitentes.pop(canal_id,None) is not None:
                self._loop(canal_id,None)
            return
        estado=self.ambientes_intermitentes.get(canal_id)
        if estado is None or estado['nome']!=nome:
            self._loop(canal_id,None)
            estado={'nome':nome,'proximo':agora+self.sorteio_ambiente.randint(1500,3500),
                    'ultimo':None}
            self.ambientes_intermitentes[canal_id]=estado
        canal=pygame.mixer.Channel(canal_id)
        if agora<estado['proximo'] or canal.get_busy():return
        info=self.catalogo['ambientes'][nome]
        arquivos=info.get('arquivos',[info['arquivo']])
        opcoes=[a for a in arquivos if a!=estado['ultimo']] or arquivos
        arquivo=self.sorteio_ambiente.choice(opcoes)
        som=self._som(arquivo)
        if som is None:
            estado['proximo']=agora+pausa_max
            return
        volume=self.master*info['volume']*self.sorteio_ambiente.uniform(.65,1)
        canal.play(som)
        canal.set_volume(volume)
        self.loops[canal_id]=nome
        self.volumes_loops[canal_id]=volume
        estado['ultimo']=arquivo
        estado['proximo']=agora+round(som.get_length()*1000)+self.sorteio_ambiente.randint(pausa_min,pausa_max)

    def _musica(self,nome,agora,reduzida=False,ganho=1):
        if nome!=self.musica_alvo:
            self.musica_alvo=nome
            self.inicio_troca=agora
            self.volume_saida=self.volume_musica
        if self.musica_atual!=self.musica_alvo:
            decorrido=max(0,agora-self.inicio_troca)
            if self.musica_atual is not None and decorrido<350 and nome not in ('guardiao','menu','combate'):
                self.volume_musica=self.volume_saida*(1-decorrido/350)
                pygame.mixer.music.set_volume(self.volume_musica)
                return
            pygame.mixer.music.stop()
            self.musica_atual=None
            if nome is not None:
                try:
                    info=self.catalogo['musicas'][nome]
                    pygame.mixer.music.load(str(self.pasta/info['arquivo']))
                    self.volume_musica=min(1,self.master*info['volume']*ganho*(.62 if reduzida and nome not in ('menu','combate') else 1))
                    pygame.mixer.music.set_volume(self.volume_musica)
                    entrada=0 if nome in ('menu','combate') else 180 if nome=='guardiao' else 650
                    pygame.mixer.music.play(info.get('repeticoes',-1),fade_ms=entrada)
                    self.musica_atual=nome
                except (pygame.error,OSError) as erro:
                    self.erros.append((nome,str(erro)))
                    logging.warning('Falha de música %s: %s',nome,erro)
                    self.musica_alvo=None
        if self.musica_atual is not None:
            volume=min(1,self.master*self.catalogo['musicas'][self.musica_atual]['volume']*ganho*(.62 if reduzida and nome not in ('menu','combate') else 1))
            if volume!=self.volume_musica:
                self.volume_musica=volume
                pygame.mixer.music.set_volume(volume)

    @staticmethod
    def perfil(jogo):
        estado=jogo.estado
        if estado in ('inicio','viagem','descoberta','chegada'):return 'menu'
        if estado=='mapa_tesouro':return 'vitoria'
        if estado=='dialogo_guardiao':return 'guardiao'
        if estado=='continuacao':return 'menu'
        if estado=='partida_final':return 'final'
        if estado=='derrota' or not jogo.kia.viva:return None
        if (getattr(jogo.ilha,'boss_ativo',False)
                and jogo.ilha.boss.vivo and estado=='exploracao'):return 'rei'
        if estado=='exploracao' and jogo.ilha.nome=='Ilha dos Macacos':return 'combate'
        return {'Ilha Afogada':'afogada','Ilha dos Macacos':'macacos',
                'Ilha da Caveira':'caveira'}[jogo.ilha.nome]

    def _passos(self,jogo,agora):
        pos=(jogo.kia.x,jogo.kia.y)
        anterior=self.ultima_posicao
        self.ultima_posicao=pos
        if (anterior is None or jogo.estado!='exploracao' or not jogo.kia.viva
                or jogo.esquivando()):
            self.proximo_passo_kia=0
            return
        distancia=math.dist(pos,anterior)
        if distancia>40:
            self.proximo_passo_kia=0
            return
        if distancia<.01:
            self.proximo_passo_kia=0
            return
        if agora<self.proximo_passo_kia:return
        self.proximo_passo_kia=agora+380
        ilha=jogo.ilha
        cais=[getattr(ilha,'cais',pygame.Rect(0,0,0,0)),getattr(ilha,'cais_final',pygame.Rect(0,0,0,0))]
        if any(r.colliderect(jogo.kia.rect) for r in cais):terreno='madeira'
        elif ilha.nome=='Ilha Afogada':
            terreno='agua' if ilha.na_agua(jogo.kia.rect) else 'areia'
        elif ilha.nome=='Ilha da Caveira':terreno='pedra'
        else:terreno='terra' if ilha.em_terra(jogo.kia.rect.inflate(60,60)) else 'areia'
        self.tocar('passo_'+terreno,agora)

    def atualizar(self,jogo,agora):
        if not self.habilitado or not pygame.mixer.get_init():return
        perfil=self.perfil(jogo)
        narrativa=(jogo.estado=='dialogo_guardiao'
                   or (agora<jogo.mensagem_ate and jogo.mensagem_narrativa))
        self._musica(perfil,agora,narrativa,ganho=1.35 if jogo.estado=='continuacao' else 1)
        mudou_ilha=self.ilha_anterior is not jogo.ilha
        mudou_estado=self.estado_anterior!=jogo.estado
        if mudou_ilha:
            self.ultima_posicao=None;self.ultima_mare=None
            self.proximo_macaco=agora+10000
            self.proxima_gaivota=agora+2500
        if mudou_estado:
            if jogo.estado=='exploracao' and self.estado_anterior=='inicio':
                self.proxima_gaivota=agora+2500
            if jogo.estado=='descoberta':self.tocar('descoberta',agora)
            elif jogo.estado=='dialogo_guardiao':self.tocar('dialogo',agora)
            elif jogo.estado=='mapa_tesouro':
                self.tocar('mapa_papel',agora);self.mapa_revelado=False
            if jogo.estado in ('viagem','partida_final'):self.proxima_remada=agora
        if self.viva_anterior and not jogo.kia.viva:self.tocar('derrota',agora)
        if (jogo.estado=='mapa_tesouro' and not self.mapa_revelado
                and agora-jogo.tela_mapa.inicio>=1600):
            self.tocar('mapa_completo',agora);self.mapa_revelado=True
        explorando=jogo.estado=='exploracao' and jogo.kia.viva
        viajando=jogo.estado in ('viagem','partida_final')
        ambiente=(explorando or viajando or jogo.estado in ('chegada','dialogo_guardiao'))
        ilha=jogo.ilha
        if ambiente:
            floresta=ilha.nome=='Ilha dos Macacos'
            sombrio=ilha.nome=='Ilha da Caveira'
            if agora>=self.proximo_ambiente:
                self.volume_mar=1 if viajando or not ilha.em_terra(jogo.kia.rect.inflate(200,200)) else .32
                self.proximo_ambiente=agora+250
            volume_mar=max(.85,self.volume_mar) if ilha.nome=='Ilha Afogada' else self.volume_mar
            if floresta and not viajando:
                # O interior da ilha 2 não recebe o chiado contínuo das ondas.
                volume_mar=.5 if self.volume_mar==1 else 0
            self._loop(0,'mar',volume_mar)
            self._ambiente_intermitente(1,'floresta' if floresta and not viajando else None,agora)
            self._ambiente_intermitente(2,None,agora)
            self._loop(2,'sombrio' if sombrio and perfil!='guardiao' else None,.6 if perfil=='rei' else 1)
            self._loop(6,None)
        else:
            for canal in (0,1,2,6):self._loop(canal,None)
            self.ambientes_intermitentes.clear()
        fogueiras=[r for nome,r in getattr(ilha,'decoracoes',[]) if nome=='fite']
        distancia=min((math.dist(jogo.kia.rect.center,r.center) for r in fogueiras),default=10000)
        self._loop(3,'fogueira' if explorando and distancia<320 else None,max(0,1-distancia/320))
        if explorando and ilha.nome=='Ilha Afogada':
            mare='subida' if ilha.subindo else 'recuo' if ilha.recuando else None
            if mare is not None and mare!=self.ultima_mare:self.tocar('mare_'+mare,agora)
            self.ultima_mare=mare
            nivel=getattr(ilha,'nivel_agua',0)
            agua=('mare_enchendo' if ilha.subindo or nivel>=1 and not ilha.recuando
                  else 'mare_recuando' if ilha.recuando else None)
            self._loop(7,agua,.65+.35*nivel)
            if agora>=self.proxima_gaivota:
                self.tocar('gaivota',agora)
                intervalo=(16000,23000,19000)[self.chamadas_gaivota%3]
                self.chamadas_gaivota+=1
                self.proxima_gaivota=agora+intervalo
        else:self._loop(7,None)
        if explorando and ilha.nome=='Ilha dos Macacos' and agora>=self.proximo_macaco:
            arvores=[r for r in ilha.arvores if r not in ilha.bananeiras_sem_macacos]
            perto=any(math.dist(jogo.kia.rect.center,r.midbottom)<500 for r in arvores)
            if perto:self.tocar('macacos',agora)
            self.proximo_macaco=agora+(26000 if perto else 4000)
        if viajando and agora>=self.proxima_remada:
            self.tocar('remada',agora);self.tocar('bote_madeira',agora)
            self.proxima_remada=agora+2200
        self._passos(jogo,agora)
        self.estado_anterior=jogo.estado
        self.ilha_anterior=ilha
        self.viva_anterior=jogo.kia.viva

    def encerrar(self):
        if self.habilitado and pygame.mixer.get_init():
            pygame.mixer.music.stop()
            for canal in range(24):pygame.mixer.Channel(canal).stop()
