"""Gera uma prévia animada das folhas usadas no jogo, sem abrir uma janela."""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')

import pygame
from PIL import Image, ImageDraw

from enemies.animacoes import carregar_animacoes


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    for nome in ('skeleton', 'pirata'):
        animacoes = carregar_animacoes(nome)
        frames = []
        for tick in range(24):
            preview = Image.new('RGB', (880, 720), (32, 51, 45))
            desenho = ImageDraw.Draw(preview)
            desenho.text((18, 12), nome.upper() + ' - animacoes', fill='white')
            for col, direcao in enumerate(('frente', 'costas', 'esquerda', 'direita')):
                desenho.text((140 + col * 180, 42), direcao, fill='white')
            for row, (acao, direcoes) in enumerate(animacoes.items()):
                y = 82 + row * 126
                desenho.text((12, y + 60), acao, fill='white')
                for col, direcao in enumerate(('frente', 'costas', 'esquerda', 'direita')):
                    quadros = direcoes[direcao]
                    indice = tick % len(quadros) if acao in ('parada', 'caminhada') else min(len(quadros) - 1, tick % 12)
                    superficie = quadros[indice]
                    imagem = Image.frombytes('RGBA', superficie.get_size(), pygame.image.tobytes(superficie, 'RGBA'))
                    preview.paste(imagem, (col * 180 + 86 - 54, y - 42), imagem)
            frames.append(preview)
        frames[0].save(f'assets/enemies/{nome}-animado/preview.gif', save_all=True,
                       append_images=frames[1:], duration=120, loop=0, disposal=2)
        frames[0].save(f'assets/enemies/{nome}-animado/preview.png')
    pygame.quit()


if __name__ == '__main__':
    main()
