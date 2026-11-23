# Caminhada revisada da Kia

> VERSÃO REVERTIDA após reprovação visual do usuário. A descrição abaixo registra a tentativa v2 e não corresponde ao jogo atual. O jogo voltou aos seis quadros anteriores, ao intervalo original de 120 ms e ao alinhamento vertical pelos pés. Apenas o alinhamento lateral da caminhada usa o topo do corpo para evitar o deslocamento produzido pelas botas. A prévia atual é `previa-caminhada-atual.gif`. Testes de código não comprovam qualidade visual da animação.

As caminhadas com e sem espada foram substituídas nas quatro direções. As folhas por direção têm duas linhas: sem espada e com espada. Os quadros separados e a ordem efetivamente usada estão em `animacoes.json`; o atlas de jogo já foi reconstruído.

O ciclo tem oito instantes. Nas vistas de frente e costas, a sequência selecionada tem três instantes de apoio de cada perna e dois de passagem. Algumas transições são reutilizadas para corrigir o apoio esquerdo antecipado das folhas geradas. Nos perfis, a perna próxima e a distante trocam a prioridade na segunda metade do ciclo.

O alinhamento preserva o registro do quadril na grade de poses. O código não recentraliza essas caminhadas pelo contorno variável das botas. A cabeça das vistas frontal e traseira varia no máximo 1 pixel horizontalmente nos quadros instalados.

Cada ciclo corresponde a 72 pixels percorridos. A fase avança pela distância real observada no desenho, conserva a passada ao mudar de direção e ignora esquivas e teletransportes. Não avança quando não há deslocamento.

As folhas e os recortes anteriores estão em `arquivo-caminhada-v1`. Os sprites foram gerados com a ferramenta integrada image_gen; os prompts e as fontes estão em `geracao-caminhada-v2.json`.

Prévia: `previa-caminhada-v2.gif`. Conferência estática: `conferencia-caminhada-v2.png`.

Validação: `python -m unittest test_caminhada_kia test_animacoes_inimigos -v` (sete testes), transparência e margens dos PNGs, atualização e renderização nas três ilhas com SDL dummy. A revisão visual foi feita pelas folhas e pelos oito quadros na escala do jogo.
