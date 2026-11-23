# Skeleton e Pirata Perdido

Cada pasta `skeleton-animado` e `pirata-animado` contém 88 quadros PNG transparentes:

| Ação | Quadros por direção |
| --- | --- |
| Parada | 4 |
| Caminhada | 6 |
| Ataque | 4: preparação, golpe, continuação e recuperação |
| Dano | 2 |
| Derrota | 6 |

Direções: frente, costas, esquerda e direita. As folhas originais estão preservadas nos arquivos `*-folha.png`. `animacoes.json` indica a ordem e os limites visíveis dos recortes.

O jogo compartilha um atlas por tipo de inimigo. O corpo mantém aproximadamente 110 pixels de altura, com os pés alinhados; cair ou agachar não aumenta o personagem. Uma assinatura dos quadros invalida o atlas quando os PNGs mudam.

Tempos: parada 200 ms por quadro; caminhada 120 ms; ataque 400 ms com impacto aos 100 ms; dano 240 ms; derrota 720 ms. O golpe causa dano uma vez e respeita esquiva e proteção. Receber dano interrompe um ataque pendente. A derrota permanece visível brevemente, sem mudar as regras de drop.

Para atualizar os atlas após editar os PNGs, inicialize o display Pygame e execute `enemies.animacoes.salvar_atlas('skeleton')` e `salvar_atlas('pirata')` em um processo novo. `python ferramentas/gerar_preview_inimigos.py` recria as prévias GIF e PNG.

Validação: `python -m unittest test_animacoes_inimigos -v`.
