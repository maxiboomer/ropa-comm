"""
Tipos de escopo.

Escopo define ONDE a permissão vale. Um usuário pode ser APROVADOR na
unidade X e VISUALIZADOR globalmente, por exemplo.
"""

from enum import Enum


class ScopeType(str, Enum):
    GLOBAL = "global"           # vale em todo o sistema
    UNIDADE = "unidade"         # filial / setor / departamento
    TIPO_OPERACAO = "tipo_op"   # restrito a certos tipos de registro
    PROPRIO = "proprio"         # só registros criados pelo próprio usuário

    def __str__(self) -> str:
        return self.value
