"""Mostra o ciclo instalado, na escala real usada pelo jogo."""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')

import pygame
from PIL import Image, ImageDraw

from characters.kia import carregar_animacoes_kia, PASTA_ANIMACOES


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    animacoes = carregar_animacoes_kia()
    frames = []
    quantidade = len(animacoes['caminhada-sem-espada']['frente'])
    for i in range(quantidade):
        quadro = Image.new('RGB', (900, 430), (34, 48, 43))
        texto = ImageDraw.Draw(quadro)
        texto.text((16, 12), f'KIA - CAMINHADA ATUAL - quadro {i + 1}/{quantidade}', fill='white')
        for linha, versao in enumerate(('sem', 'com')):
            texto.text((15, 100 + linha * 190), versao + ' espada', fill='white')
            for coluna, direcao in enumerate(('frente', 'costas', 'esquerda', 'direita')):
                sprite = animacoes[f'caminhada-{versao}-espada'][direcao][i]
                imagem = Image.frombytes('RGBA', sprite.get_size(), pygame.image.tobytes(sprite, 'RGBA'))
                x, y = 84 + coluna * 200, 35 + linha * 190
                texto.line((x + 40, y + 166, x + 155, y + 166), fill=(75, 95, 78))
                texto.text((x + 68, y + 12), direcao, fill='white')
                quadro.paste(imagem, (x, y), imagem)
        frames.append(quadro)
    frames[0].save(PASTA_ANIMACOES / 'previa-caminhada-atual.gif', save_all=True,
                   append_images=frames[1:], duration=85, loop=0, disposal=2)
    # Todos os quadros em uma planta estática para revisão das transições.
    grade = Image.new('RGB', (1800, ((quantidade + 1) // 2) * 430))
    for i, frame in enumerate(frames):
        grade.paste(frame, ((i % 2) * 900, (i // 2) * 430))
    grade.save(PASTA_ANIMACOES / 'conferencia-caminhada-atual.png')
    pygame.quit()


if __name__ == '__main__':
    main()
