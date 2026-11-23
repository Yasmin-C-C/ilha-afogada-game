# A Ilha Afogada

Jogo de aventura em três ilhas, desenvolvido em Python e Pygame.

## Executar

Na pasta `Codigo`:

```powershell
python -m pip install -r requirements.txt
python main.py
```

O jogo carrega os recursos de `assets/`, independentemente da pasta de onde foi iniciado.

## Controles

- W, A, S e D: movimentar Kia.
- Espaço: atacar após coletar a espada.
- Shift: esquivar.
- E: interagir.
- Setas, Enter e mouse: navegar pelos menus.
- Esc: fechar uma narrativa ou sair, conforme a tela.

## Estrutura

- `main.py`: fluxo da partida, transições e interações.
- `characters/`: Kia e suas animações.
- `enemies/`: skeletons, piratas e quadros compartilhados.
- `scenes/`: cenários, maré e regras de cada ilha.
- `audio_jogo.py`: músicas, ambientes e efeitos.
- `hud.py` e módulos de telas: apresentação e interface.
- `assets/`: imagens, animações, narrativa, áudio e créditos.
- `ferramentas/`: preparação de recursos e geração de prévias; não é executada na partida.

As ferramentas de edição de imagens e áudio precisam das dependências opcionais em `requirements-ferramentas.txt`. Os caminhos das fontes de áudio são passados a `ferramentas/preparar_audio.py`; os arquivos exportados já estão incluídos no jogo. Preserve os créditos e as licenças ao distribuir.


