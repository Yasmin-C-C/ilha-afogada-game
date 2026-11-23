"""Prepara as fontes licenciadas; requer numpy e soundfile apenas nesta etapa.

Uso: python preparar_audio.py PASTA_DAS_FONTES --ferramentas PASTA_DOS_MODULOS
O jogo usa somente pygame e os arquivos exportados em assets/audio.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import subprocess
from zipfile import ZipFile

parser=argparse.ArgumentParser()
parser.add_argument('fontes',type=Path)
parser.add_argument('--ferramentas',type=Path)
args=parser.parse_args()
if args.ferramentas:sys.path.insert(0,str(args.ferramentas))
import numpy as np
import soundfile as sf

DESTINO=Path(__file__).resolve().parents[1]/'assets/audio'
DESTINO.mkdir(parents=True,exist_ok=True)
REGISTROS=[]
TAXA=44100
MANIFESTO=DESTINO/'fontes.json'
ANTERIORES=({r['arquivo']:r for r in json.loads(MANIFESTO.read_text(encoding='utf-8'))['arquivos']}
            if MANIFESTO.exists() else {})

FONTES={
 'rpg':('Kenney','CC0-1.0','https://kenney.nl/assets/rpg-audio'),
 'interface':('Kenney','CC0-1.0','https://kenney.nl/assets/interface-sounds'),
 'impact':('Kenney','CC0-1.0','https://kenney.nl/assets/impact-sounds'),
 'fantasy':('North Fantasy Music','CC-BY-4.0','https://opengameart.org/content/fantasy-music-and-drum-loops-pack'),
 'pirate':('Eldritch Grim','CC0-1.0','https://opengameart.org/content/pirate-adventure'),
 'boss_pixabay':('Alec_Koff - Epic Fight','Pixabay Content License','https://pixabay.com/music/adventure-epic-fight-487416/'),
 'combates_usuario':('Arquivo combates.mp3 enviado pelo usuário','Fornecido pelo usuário','combates.mp3'),
 'menu_usuario':('Arquivo menu.mp3 enviado pelo usuário','Fornecido pelo usuário','menu.mp3'),
 'ilha3_usuario':('Arquivo ilha 3.mp3 enviado pelo usuário','Fornecido pelo usuário','ilha 3.mp3'),
 'waves':('jasinski; edição original qubodup','CC0-1.0','https://opengameart.org/content/beach-ocean-waves'),
 'mar_longo':('rucisko - ocean waves 01','CC0-1.0','https://freesound.org/people/rucisko/sounds/164767/'),
 'fire':('PagDev','CC0-1.0','https://opengameart.org/content/fireplace-sound-loop'),
 'wind':('remaxim','CC0-1.0','https://opengameart.org/content/short-wind-sound'),
 'birds':('isaiah658','CC0-1.0','https://opengameart.org/content/ambient-bird-sounds'),
 'dungeon':('JaggedStone','CC0-1.0','https://opengameart.org/content/loopable-dungeon-ambience'),
 'magic':('JaggedStone','CC0-1.0','https://opengameart.org/node/29772'),
 'voices':('Cici Fyre (cicifyre)','CC0-1.0','https://opengameart.org/content/female-rpg-voice-starter-pack'),
 'water':('rubberduck','CC0-1.0','https://opengameart.org/content/40-cc0-water-splash-slime-sfx'),
 'crickets':('dklon','CC-BY-3.0','https://opengameart.org/content/crickets'),
 'monkeys':('Radio_fragola_gorizia','CC0-1.0','https://freesound.org/people/Radio_fragola_gorizia/sounds/400086/'),
 'seagulls':('Lydmakeren','CC0-1.0','https://freesound.org/people/Lydmakeren/sounds/510917/'),
 'bones':('spookymodem','CC-BY-3.0','https://opengameart.org/content/rattling-bones'),
 'crunch':('spookymodem','CC-BY-3.0','https://opengameart.org/content/crunching-bones'),
 'laugh':('Venn Stone','CC0-1.0','https://opengameart.org/content/evil-laughter-0'),
 'dark_magic':('qubodup','CC0-1.0','https://opengameart.org/content/3-dark-magic-spells'),
 'male_pain':('Michel Baradari','CC-BY-3.0','https://opengameart.org/content/11-male-human-paindeath-sounds'),
 'flood':('KevinT1001','CC0-1.0','https://freesound.org/people/KevinT1001/sounds/379906/'),
 'male_grunts':('HaelDB','CC0-1.0','https://opengameart.org/content/male-gruntyelling-sounds'),
 'projeto':('A Ilha Afogada - síntese sonora do projeto','Produção do projeto','ferramentas/preparar_audio.py'),
 'vitoria_mapa':('Umplix','CC0-1.0','https://opengameart.org/content/victory-4'),
 'vitoria_chave':('ARoachIFoundOnMyPillow','CC0-1.0','https://opengameart.org/content/victory-fanfare'),
}


def ler(arquivo,membro=None,mono=True):
    if membro and arquivo.endswith('.7z'):
        dados=subprocess.check_output(['C:/Windows/System32/tar.exe','-xOf',str(args.fontes/arquivo),membro])
    elif membro:
        with ZipFile(args.fontes/arquivo) as z:dados=z.read(membro)
    else:dados=(args.fontes/arquivo).read_bytes()
    x,sr=sf.read(io.BytesIO(dados),dtype='float32',always_2d=True)
    if mono:x=x.mean(axis=1,keepdims=True)
    if sr!=TAXA:
        t=np.arange(round(len(x)*TAXA/sr))*sr/TAXA
        x=np.stack([np.interp(t,np.arange(len(x)),x[:,c]) for c in range(x.shape[1])],axis=1)
    return x.astype('float32'),[{'arquivo_original':arquivo,'membro':membro,
                              'sha256_original':hashlib.sha256(dados).hexdigest()}]


def normalizar(x,pico=.75,rms=None):
    pico_atual=float(np.max(np.abs(x)))
    if pico_atual<.00001:raise ValueError('Fonte silenciosa')
    ganho=pico/pico_atual
    if rms:ganho=min(ganho,rms/max(.00001,float(np.sqrt(np.mean(x*x)))))
    return x*min(ganho,4)


def trecho(x,segundos=None,inicio=0):
    return x[round(inicio*TAXA):round((inicio+segundos)*TAXA) if segundos else None].copy()


def fade(x,segundos=.008):
    n=min(round(segundos*TAXA),len(x)//2)
    if n:
        r=np.linspace(0,1,n,dtype='float32')[:,None]
        x[:n]*=r;x[-n:]*=r[::-1]
    return x


def loop(x,sobreposicao=.35,potencia_constante=False):
    n=min(round(sobreposicao*TAXA),len(x)//4)
    r=np.linspace(0,1,n,dtype='float32')[:,None]
    if potencia_constante:
        uniao=x[-n:]*np.cos(r*np.pi/2)+x[:n]*np.sin(r*np.pi/2)
    else:
        uniao=x[-n:]*(1-r)+x[:n]*r
    return np.concatenate((x[n:-n],uniao))


def exportar(nome,x,origens,fontes,modificacao):
    x=np.asarray(x,dtype='float32')
    if not np.isfinite(x).all() or len(x)<100:raise ValueError(nome)
    if float(np.max(np.abs(x)))>=1:raise ValueError('Clipping: '+nome)
    anterior=ANTERIORES.get(nome)
    caminho=DESTINO/nome
    segundos=round(len(x)/TAXA,3)
    # Preserva arquivos idênticos, inclusive músicas abertas pelo jogo no Windows.
    if (anterior and caminho.exists() and anterior['segundos']==segundos
            and anterior['origens']==origens and anterior['fontes']==fontes
            and anterior['alteracoes']==modificacao
            and hashlib.sha256(caminho.read_bytes()).hexdigest()==anterior['sha256']):
        REGISTROS[:]=[r for r in REGISTROS if r['arquivo']!=nome]
        REGISTROS.append(anterior)
        return
    # Blocos pequenos evitam sobrecarregar o encoder Vorbis no Windows.
    with sf.SoundFile(DESTINO/nome,'w',samplerate=TAXA,channels=x.shape[1],
                      subtype='VORBIS' if nome.endswith('.ogg') else 'PCM_16') as saida:
        for inicio in range(0,len(x),4096):saida.write(x[inicio:inicio+4096])
    REGISTROS[:]=[r for r in REGISTROS if r['arquivo']!=nome]
    REGISTROS.append({'arquivo':nome,'segundos':segundos,
        'fontes':fontes,'origens':origens,'alteracoes':modificacao,
        'sha256':hashlib.sha256((DESTINO/nome).read_bytes()).hexdigest()})


def efeito(nome,pacote,membro,fonte,limite=None):
    x,origens=ler(pacote,membro)
    ativos=np.flatnonzero(np.max(np.abs(x),axis=1)>.002)
    if len(ativos):x=x[max(0,ativos[0]-440):min(len(x),ativos[-1]+2205)]
    if limite:x=trecho(x,limite)
    exportar(nome,fade(normalizar(x)),origens,[fonte],'Recorte de silêncio, normalização, fade curto; WAV mono 44,1 kHz.')


EFEITOS={}
def registrar(chave,arquivos,volume,intervalo=100):
    EFEITOS[chave]={'arquivos':arquivos,'volume':volume,'intervalo_ms':intervalo}


def preparar_passo(x,limite):
    # Algumas fontes têm picos muito baixos; o limite de ganho dos outros
    # efeitos deixava esses passos inaudíveis sob a música.
    pico=float(np.max(np.abs(x)))
    if pico<.00001:raise ValueError('Passo silencioso')
    ativos=np.flatnonzero(np.max(np.abs(x),axis=1)>pico*.025)
    x=x[max(0,ativos[0]-round(.005*TAXA)):min(len(x),ativos[-1]+round(.025*TAXA))]
    x=fade(trecho(x,limite),.002)
    ganho=min(.85/float(np.max(np.abs(x))),.16/max(.00001,float(np.sqrt(np.mean(x*x)))))
    return x*ganho


for n in (1,2):
    efeito(f'espada-{n}.wav','rpg-audio.zip',f'Audio/knifeSlice{"2" if n==2 else ""}.ogg','rpg')
    efeito(f'dano-{n}.wav','voices.zip',f'RPG Voice Starter Pack/Type 3/damaged{n}.wav','voices',1.2)
    efeito(f'impacto-{n}.wav','impact-sounds.zip',f'Audio/impactWood_heavy_00{n-1}.ogg','impact')
registrar('espada',['espada-1.wav','espada-2.wav'],.42,150)
registrar('dano',['dano-1.wav','dano-2.wav'],.40,350)
registrar('inimigo_dano',['impacto-1.wav','impacto-2.wav'],.43,70)

for n in range(1,5):
    for terreno,prefixo in (
        ('areia','footstep_snow_00'),('terra','footstep_grass_00'),
        ('pedra','footstep_concrete_00'),('madeira','footstep_wood_00')):
        x,o=ler('impact-sounds.zip',f'Audio/{prefixo}{n-1}.ogg')
        exportar(f'passo-{terreno}-{n}.wav',preparar_passo(x,.4),o,['impact'],
                 'Passo com recorte de silêncio, fade de 2 ms e ganho por pico/RMS aplicado após o fade; WAV mono 44,1 kHz.')
    x,o=ler('water.zip',f'splash_0{n}.ogg')
    exportar(f'passo-agua-{n}.wav',preparar_passo(x,.32),o,['water'],
             'Respingo curto para passo na água; recorte, fade de 2 ms e ganho por pico/RMS aplicado após o fade; WAV mono 44,1 kHz.')
for terreno in ('areia','terra','pedra','madeira','agua'):
    registrar('passo_'+terreno,[f'passo-{terreno}-{n}.wav' for n in range(1,5)],
              .24 if terreno!='agua' else .27,320)

for nome,pacote,membro,fonte,volume,limite in (
 ('morte','impact-sounds.zip','Audio/impactWood_heavy_003.ogg','impact',.4,1),
 ('coleta','interface-sounds.zip','Audio/confirmation_002.ogg','interface',.34,1.2),
 ('bau','rpg-audio.zip','Audio/doorOpen_1.ogg','rpg',.34,2),
 ('esquiva','rpg-audio.zip','Audio/cloth1.ogg','rpg',.36,.6),
 ('menu_selecao','interface-sounds.zip','Audio/click_003.ogg','interface',.22,.5),
 ('menu_confirmar','interface-sounds.zip','Audio/confirmation_001.ogg','interface',.28,.8),
 ('mapa_papel','rpg-audio.zip','Audio/bookOpen.ogg','rpg',.3,1.5),
 ('dialogo','rpg-audio.zip','Audio/bookFlip1.ogg','rpg',.18,1),
 ('bote_madeira','rpg-audio.zip','Audio/creak1.ogg','rpg',.2,2),
 ('remada','water.zip','splash_08.ogg','water',.25,1.2),
 ('rei_impacto','impact-sounds.zip','Audio/impactPunch_heavy_000.ogg','impact',.48,1.2),
):
    efeito(nome+'.wav',pacote,membro,fonte,limite)
    registrar(nome,[nome+'.wav'],volume,150 if nome!='bote_madeira' else 2500)
for nome,fonte_arq,limite,volume in (
 ('rei_invocacao','magical_4.ogg',2.5,.33),
 ('surgimento','magical_2.ogg',1.6,.32),
 ('rei_derrota','magical_7.ogg',3.8,.44),
 ('descoberta','magical_5.ogg',2.2,.28),
 ('mapa_completo','magical_6.ogg',2.5,.36),
 ('derrota','magical_3.ogg',2,.32),
):
    x,o=ler(fonte_arq)
    exportar(nome+'.wav',fade(normalizar(trecho(x,limite))),o,['magic'],'Recorte, normalização e fade; WAV mono 44,1 kHz.')
    registrar(nome,[nome+'.wav'],volume,1000)
x,o=ler('wind.wav')
exportar('rei-preparacao.wav',fade(normalizar(trecho(x,.5,inicio=.2))),o,['wind'],'Trecho curto do vento para preparação do golpe; normalização e fade.')
registrar('rei_preparacao',['rei-preparacao.wav'],.24,800)

MUSICAS={}
for chave,arquivo,membro,fonte,volume in (
 ('menu','menu-usuario.mp3',None,'menu_usuario',.48),
 ('afogada','fantasyambience.zip','FantasyAmbience/Nightwatch.wav','fantasy',.18),
 ('macacos','pirate_adventure.wav',None,'pirate',.22),
 ('caveira','ilha 3.mp3',None,'ilha3_usuario',.26),
 ('guardiao','fantasyambience.zip','FantasyAmbience/Temple_of_Light.wav','fantasy',.30),
 ('rei','epic-fight-487416.mp3',None,'boss_pixabay',.27),
 ('combate','combates-usuario.mp3',None,'combates_usuario',.50),
 ('final','victory-music.wav',None,'vitoria_mapa',.42),
 ('vitoria','victory-music.wav',None,'vitoria_mapa',.34),
):
    x,o=ler(arquivo,membro,mono=False)
    alteracoes='Normalização com limite de pico, fade de 20 ms nas extremidades; OGG Vorbis estéreo 44,1 kHz.'
    if chave in ('guardiao','menu'):
        ativos=np.flatnonzero(np.max(np.abs(x),axis=1)>.004)
        if len(ativos):x=x[max(0,ativos[0]-round(.02*TAXA)):]
        alteracoes+=' Silêncio inicial removido para entrada imediata.'
    if chave=='combate':
        previa=normalizar(x,pico=.85,rms=.13)
        janela=round(.1*TAXA)
        inicio=next(k for k in range(0,len(previa)-janela,janela)
                    if float(np.sqrt(np.mean(previa[k:k+janela]**2)))>=.04)
        x=x[max(0,inicio-round(.005*TAXA)):]
        alteracoes+=' Introdução de baixo volume recortada para começar no primeiro trecho forte.'
    borda=.005 if chave in ('menu','combate') else .02
    if chave in ('menu','combate'):alteracoes=alteracoes.replace('20 ms','5 ms')
    nome={'rei':'musica-rei-epic-fight.ogg','menu':'musica-menu-imediata.ogg','final':'musica-final-vitoria.ogg',
          'combate':'musica-combate-imediata.ogg'}.get(chave,'musica-'+chave+'.ogg')
    exportar(nome,fade(normalizar(x,pico=.85,rms=.13),borda),o,[fonte],alteracoes)
    MUSICAS[chave]={'arquivo':nome,'volume':volume}
MUSICAS['vitoria']['repeticoes']=0

AMBIENTES={}
x,o=ler('ocean-waves-long.mp3')
mar=loop(normalizar(trecho(x,60,inicio=8),pico=.7,rms=.12),
         sobreposicao=3,potencia_constante=True)
exportar('ambiente-mar-continuo.ogg',normalizar(mar,pico=.7,rms=.12),o,['mar_longo'],
         'Trecho contínuo de 60 s; mono, normalização e crossfade de potência constante de 3 s para loop sem queda de volume.')
AMBIENTES['mar']={'arquivo':'ambiente-mar-continuo.ogg','volume':.24}
for chave,arq,fonte,duracao,inicio,volume in (
 ('sombrio','dungeon.ogg','dungeon',24,8,.15),
 ('fogueira','fire.wav','fire',18,2,.25),
 ('insetos','crickets.mp3','crickets',16,1,.055),
):
    x,o=ler(arq)
    nome='ambiente-'+chave+'.ogg'
    exportar(nome,loop(normalizar(trecho(x,duracao,inicio),pico=.7,rms=.12)),o,[fonte],
             'Trecho mono, normalização e emenda com crossfade de 350 ms para repetição; OGG Vorbis.')
    AMBIENTES[chave]={'arquivo':nome,'volume':volume}
for chave,arq,fonte,trechos,volume,borda in (
 ('floresta','birds.ogg','birds',((4,1.8),(11,2.1),(19,2.4),(27,1.9)),.075,.12),
):
    x,o=ler(arq)
    arquivos=[]
    for n,(inicio,duracao) in enumerate(trechos,1):
        nome='ambiente-'+chave+('' if n==1 else '-'+str(n))+'.ogg'
        som=fade(normalizar(trecho(x,duracao,inicio),pico=.6,rms=.09),borda)
        exportar(nome,som,o,[fonte],
                 'Trecho curto mono, normalização e fades suaves; reprodução sem loop, com variações e pausas irregulares controladas pelo jogo; OGG Vorbis.')
        arquivos.append(nome)
    AMBIENTES[chave]={'arquivo':arquivos[0],'arquivos':arquivos,'volume':volume}
# A água em movimento permanece audível durante toda a subida/recuo, inclusive
# os 12 segundos da primeira enchente. A emenda permite repetir sem estalos.
for chave,inicio,volume in (('mare_enchendo',2,.34),('mare_recuando',14,.28)):
    x,o=ler('flood.mp3')
    ondas,oo=ler('waves.flac')
    corrente=normalizar(trecho(x,12,inicio),pico=.7,rms=.18)
    ondas=np.resize(normalizar(ondas,pico=.7,rms=.15),corrente.shape)
    agua=normalizar(corrente*.8+ondas*.2,pico=.75,rms=.18)
    nome='ambiente-'+chave+'.ogg'
    exportar(nome,loop(agua),o+oo,['flood','waves'],
             'Correnteza de enchente com 20% de ondas do mar, normalização e crossfade de 350 ms; OGG mono.')
    AMBIENTES[chave]={'arquivo':nome,'volume':volume}
x,o=ler('seagulls.mp3')
for n,inicio in enumerate((1,5,9),1):
    nome=f'gaivota-{n}.wav'
    exportar(nome,fade(normalizar(trecho(x,3.5,inicio),pico=.7,rms=.13),.12),o,['seagulls'],
             'Trecho da prévia pública em MP3; normalização, mistura mono e fades de 120 ms.')
registrar('gaivota',[f'gaivota-{n}.wav' for n in (1,2,3)],.23,12000)
x,o=ler('waves.flac')
for nome,reverter in (('mare_subida',False),('mare_recuo',True)):
    amostra=trecho(x,5)
    if reverter:amostra=amostra[::-1].copy()
    exportar(nome+'.wav',fade(normalizar(amostra,pico=.7,rms=.15),.5),o,['waves'],
             'Trecho de onda, normalização, fade de 500 ms; recuo reproduzido ao contrário.')
    registrar(nome,[nome+'.wav'],.31 if not reverter else .24,1200)
x,o=ler('monkeys.mp3')
exportar('macacos.wav',fade(normalizar(trecho(x,6,inicio=3),pico=.7,rms=.1),.1),o,['monkeys'],
         'Trecho da prévia pública em MP3, normalizado e convertido em WAV mono; fades de 100 ms.')
registrar('macacos',['macacos.wav'],.13,18000)

# Identidades sonoras do combate: vozes não verbais e efeitos separados por ator.
def velocidade(x,fator):
    t=np.arange(0,len(x),fator)
    return np.stack([np.interp(t,np.arange(len(x)),x[:,c])
                     for c in range(x.shape[1])],axis=1).astype('float32')


def eco_sombrio(x):
    saida=np.zeros((len(x)+round(.34*TAXA),x.shape[1]),dtype='float32')
    for segundos,ganho in ((0,1),(.11,.24),(.23,.12),(.34,.055)):
        k=round(segundos*TAXA);saida[k:k+len(x)]+=x*ganho
    return saida


def voz(nome,arquivo,membro,fonte,segundos,fator,volume):
    x,o=ler(arquivo,membro)
    x=fade(normalizar(eco_sombrio(velocidade(trecho(x,segundos),fator))))
    exportar(nome+'.wav',x,o,[fonte],'Recorte, alteração de altura por velocidade, ecos curtos, normalização e fades.')
    registrar(nome,[nome+'.wav'],volume,500)


for n in (1,2):
    x,o=ler('rpg-audio.zip',f'Audio/knifeSlice{"2" if n==2 else ""}.ogg')
    exportar(f'espada-{n}.wav',fade(normalizar(velocidade(x,1.16))),o,['rpg'],
             'Golpe acelerado em 16% para timbre mais agudo e afiado; normalização e fades.')
    efeito(f'kia-urro-ataque-{n}.wav','voices.zip',f'RPG Voice Starter Pack/Type 3/attack{n}.wav','voices',.7)
    efeito(f'kia-urro-esquiva-{n}.wav','voices.zip',f'RPG Voice Starter Pack/Type 3/jump{n}.wav','voices',.55)
    x,o=ler('bones-crunch.wav')
    metade=len(x)//2;janela=round(.45*TAXA);inicio=(n-1)*metade
    candidatos=range(inicio,max(inicio+1,min(len(x)-janela,n*metade)),2205)
    inicio=max(candidatos,key=lambda k:float(np.mean(x[k:k+janela]**2)))
    exportar(f'skeleton-dano-{n}.wav',fade(normalizar(x[inicio:inicio+janela].copy())),o,['crunch'],
             'Estalo de ossos selecionado por energia em cada metade; normalização e fade curto.')
    x,o=ler('rpg-audio.zip',f'Audio/knifeSlice{"2" if n==2 else ""}.ogg')
    exportar(f'skeleton-espada-{n}.wav',fade(normalizar(velocidade(x,.88))),o,['rpg'],
             'Golpe de espada com timbre mais grave que a espada de Kia.')
    x,o=ler('bones.wav')
    # Seleciona um pequeno chocalho audível em cada metade da gravação.
    metade=len(x)//2;janela=round(.28*TAXA);inicio=(n-1)*metade
    candidatos=range(inicio,max(inicio+1,min(len(x)-janela,n*metade)),2205)
    inicio=max(candidatos,key=lambda k:float(np.mean(x[k:k+janela]**2)))
    exportar(f'skeleton-ossos-{n}.wav',fade(normalizar(x[inicio:inicio+janela].copy(),pico=.65)),o,['bones'],
             'Trecho curto de ossos batendo, selecionado por energia; normalização e fade.')
    voz(f'rei_dano_{n}','male-pain.7z','player/painh.wav' if n==1 else 'player/pain3.wav',
        'male_pain',.48,.76,.38)
efeito('kia-grito-ataque.wav','voices.zip','RPG Voice Starter Pack/Type 3/attack3.wav','voices',.5)
registrar('kia_grito_ataque',['kia-grito-ataque.wav'],.54,250)
registrar('kia_urro_ataque',[f'kia-urro-ataque-{n}.wav' for n in (1,2)],.50,250)
registrar('kia_urro_esquiva',[f'kia-urro-esquiva-{n}.wav' for n in (1,2)],.33,900)
registrar('skeleton_dano',[f'skeleton-dano-{n}.wav' for n in (1,2)],.43,90)
registrar('skeleton_espada',[f'skeleton-espada-{n}.wav' for n in (1,2)],.34,100)
registrar('skeleton_ossos',[f'skeleton-ossos-{n}.wav' for n in (1,2)],.16,320)
for n in (1,2):
    voz(f'skeleton-derrota-{n}','male-pain.7z',f'player/die{n}.wav',
        'male_pain',1.2,.80,.36)
    EFEITOS.pop(f'skeleton-derrota-{n}')
registrar('skeleton_derrota',[f'skeleton-derrota-{n}.wav' for n in (1,2)],.36,0)
# Mesma voz masculina nas variações de esforço e grito do pirata.
for n,membro in enumerate(('3grunt3.wav','3grunt4.wav','3yell12.wav'),1):
    efeito(f'pirata-ataque-{n}.wav','male-grunts.zip','yelling sounds/'+membro,'male_grunts',.75)
registrar('pirata_ataque',[f'pirata-ataque-{n}.wav' for n in (1,2,3)],.48,180)
efeito('pirata-dano.wav','male-grunts.zip','yelling sounds/3grunt5.wav','male_grunts',.65)
registrar('pirata_dano',['pirata-dano.wav'],.40,180)
for n,membro in enumerate(('3yell1.wav','3yell6.wav'),1):
    efeito(f'pirata-derrota-{n}.wav','male-grunts.zip','yelling sounds/'+membro,'male_grunts',2.5)
registrar('pirata_derrota',[f'pirata-derrota-{n}.wav' for n in (1,2)],.48,0)
voz('rei_urro','male-grunts.zip','yelling sounds/3grunt6.wav','male_grunts',1.5,.72,.44)
voz('rei_grito','male-grunts.zip','yelling sounds/3yell14.wav','male_grunts',2,.80,.46)
# Aparição dos mortos: magia grave com ossos puxados do chão.
x,o=ler('dark_magic.7z','dark_magic/fout-01.flac')
magia=velocidade(trecho(x,2),.78)
ossos,oo=ler('bones-crunch.wav')
janela=round(.8*TAXA)
k=max(range(0,max(1,len(ossos)-janela),2205),key=lambda k:float(np.mean(ossos[k:k+janela]**2)))
ossos=fade(normalizar(ossos[k:k+janela][::-1].copy(),pico=.5))
magia=normalizar(magia,pico=.65)
magia[:len(ossos)]+=ossos*.25
exportar('surgimento.wav',fade(normalizar(eco_sombrio(magia))),o+oo,['dark_magic','crunch'],
         'Magia grave desacelerada, ossos invertidos e eco curto para aparição necromântica; normalização e fades.')
registrar('surgimento',['surgimento.wav'],.38,800)
# Queda melancólica em ré menor, com timbre suave e cauda que desaparece.
duracao=3.6
t=np.arange(round(duracao*TAXA),dtype='float32')/TAXA
triste=np.zeros_like(t)
for inicio,frequencia in ((0,293.6648),(.45,220),(.9,174.6141),(1.35,146.8324)):
    tempo=np.maximum(0,t-inicio)
    envelope=(1-np.exp(-tempo*45))*np.exp(-tempo*2.3)*(t>=inicio)
    triste+=envelope*(np.sin(2*np.pi*frequencia*tempo)+.16*np.sin(4*np.pi*frequencia*tempo))*.22
triste+=np.sin(2*np.pi*73.4162*t)*(1-np.exp(-t*8))*np.exp(-t*1.2)*.05
exportar('derrota.wav',fade(normalizar(triste[:,None],pico=.65,rms=.14),.12),[],['projeto'],
         'Composição original sintetizada: notas descendentes de ré menor, ataque suave e decaimento; WAV mono.')
registrar('derrota',['derrota.wav'],.34,1000)
x,o=ler('victory-key.wav')
exportar('vitoria-chave.wav',fade(normalizar(trecho(x,3.2),pico=.75,rms=.17),.18),o,['vitoria_chave'],
         'Trecho curto de fanfarra de vitória, mistura mono, normalização e fades de 180 ms.')
registrar('vitoria_chave',['vitoria-chave.wav'],.46,1000)
# Os dois arquivos de voz são variantes do mesmo evento de dano.
EFEITOS.pop('rei_dano_1');EFEITOS.pop('rei_dano_2')
registrar('rei_dano',['rei_dano_1.wav','rei_dano_2.wav'],.38,380)
voz('rei_risada','evil-laugh.flac',None,'laugh',3,.82,.34)
voz('rei_derrota','male-pain.7z','player/deathh.wav','male_pain',1,.65,.50)
x,o=ler('dark_magic.7z','dark_magic/fout-03.flac')
exportar('rei_invocacao.wav',fade(normalizar(trecho(x,2.3))),o,['dark_magic'],
         'Trecho de magia sombria, normalizado e com fades; WAV mono.')
registrar('rei_invocacao',['rei_invocacao.wav'],.35,3000)
# Três cortes secos em rápida sucessão dão às garras uma assinatura própria.
x,o=ler('rpg-audio.zip','Audio/knifeSlice2.ogg')
y,oy=ler('rpg-audio.zip','Audio/cloth2.ogg')
corte=velocidade(trecho(x,.3),.84)
garras=np.zeros((len(corte)+round(.12*TAXA),1),dtype='float32')
for atraso,ganho in ((0,.8),(.055,.5),(.12,.35)):
    k=round(atraso*TAXA);garras[k:k+len(corte)]+=corte*ganho
tecido=trecho(y,min(.35,len(garras)/TAXA))
garras[:len(tecido)]+=tecido*.3
exportar('rei_impacto.wav',fade(normalizar(garras)),o+oy,['rpg'],
         'Três cortes em camadas, timbre grave e tecido rasgando para o golpe de garras.')
registrar('rei_impacto',['rei_impacto.wav'],.46,500)

(DESTINO/'catalogo.json').write_text(json.dumps({'musicas':MUSICAS,'ambientes':AMBIENTES,'efeitos':EFEITOS},ensure_ascii=False,indent=2),encoding='utf-8')
(DESTINO/'fontes.json').write_text(json.dumps({'data':'2026-11-23','fontes':{
    k:{'autor':a,'licenca':l,'url':u} for k,(a,l,u) in FONTES.items()},'arquivos':REGISTROS},ensure_ascii=False,indent=2),encoding='utf-8')
licencas=DESTINO/'licencas';licencas.mkdir(exist_ok=True)
for pack in ('rpg-audio','interface-sounds','impact-sounds'):
    with ZipFile(args.fontes/(pack+'.zip')) as z:
        (licencas/(pack+'-CC0.txt')).write_bytes(z.read('License.txt'))
creditos=['A ILHA AFOGADA - CRÉDITOS DE ÁUDIO','',
    'Passos de areia, terra, pedra e madeira: Impact Sounds, de Kenney (CC0 1.0).',
    'https://kenney.nl/assets/impact-sounds',
    'Quatro variações por superfície, recorte, ganho por pico/RMS e fades curtos.',
    'Passos na água: respingos de rubberduck, 40 CC0 water/splash/slime SFX (CC0 1.0).',
    'https://opengameart.org/content/40-cc0-water-splash-slime-sfx', '',
    'Música: North Fantasy Music - Fantasy Music and Drum Loops Pack.',
    'Faixas: Nightwatch e Temple of Light.',
    'Licença CC BY 4.0: https://creativecommons.org/licenses/by/4.0/',
    'https://opengameart.org/content/fantasy-music-and-drum-loops-pack',
    'Alterações: normalização, fades curtos e conversão WAV para OGG.', '',
    'Insetos: Crickets, de dklon.',
    'Licença CC BY 3.0: https://creativecommons.org/licenses/by/3.0/',
    'https://opengameart.org/content/crickets',
    'Alterações: recorte, normalização, mistura mono e emenda para repetição.', '',
    'Ossos: Rattling Bones e Crunching Bones, de spookymodem.',
    'Reações de dor: 11 male human pain/death sounds, de Michel Baradari.',
    'Licença CC BY 3.0: https://creativecommons.org/licenses/by/3.0/',
    'https://opengameart.org/content/rattling-bones',
    'https://opengameart.org/content/crunching-bones',
    'https://opengameart.org/content/11-male-human-paindeath-sounds',
    'Alterações: recortes, ajuste de timbre, ecos, normalização e fades.', '',
    'Música do Rei Necromante: Epic Fight - Alec_Koff (Pixabay, ID 487416).',
    'https://pixabay.com/music/adventure-epic-fight-487416/',
    'Pixabay Content License: https://pixabay.com/service/license-summary/',
    'A página informa registro no YouTube Content ID.',
    'Alterações: normalização, fades curtos e conversão MP3 para OGG.', '',
    'Música dos demais combates: combates.mp3, fornecida pelo usuário.',
    'Convertida para OGG com normalização e fades curtos; origem/licença não inferidas.', '',
    'Música do menu e transições entre ilhas: menu.mp3, fornecida pelo usuário.',
    'Convertida para OGG com normalização e fades curtos; origem/licença não inferidas.', '',
    'Música da Ilha da Caveira até a arena do Rei: ilha 3.mp3, fornecida pelo usuário.',
    'Convertida para OGG com normalização e fades curtos; origem/licença não inferidas.', '',
    'Efeito de derrota: composição original do projeto, sintetizada em ré menor.', '',
    'Outros efeitos e ambientes relacionados abaixo: CC0 1.0.',
    'https://creativecommons.org/publicdomain/zero/1.0/','']
for chave,(autor,licenca,url) in FONTES.items():
    if licenca=='CC0-1.0':creditos.extend((autor+' - '+url,))
creditos.extend(('', 'Detalhes por arquivo, alterações e hashes de integridade: fontes.json.',
    'Preservar este arquivo e as licenças ao distribuir o jogo.'))
(DESTINO/'CREDITOS.txt').write_text('\n'.join(creditos)+'\n',encoding='utf-8')
print('Preparados',len(REGISTROS),'arquivos;',round(sum((DESTINO/r['arquivo']).stat().st_size for r in REGISTROS)/1024**2,2),'MiB')
