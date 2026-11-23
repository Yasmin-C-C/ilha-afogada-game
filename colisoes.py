"""Regras de bloqueio compartilhadas pela movimentação dos personagens."""


def bloqueia_movimento(pes, corpo, obstaculos):
    for tipo, rect in obstaculos:
        area = (corpo if tipo == 'inimigo' else
                corpo.union(pes) if tipo in ('chave', 'frasco') else pes)
        if area.colliderect(rect):
            return True
    return False
