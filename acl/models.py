"""
Models SQLAlchemy para a parte persistida da ACL.

Os PAPÉIS ficam em código (enum Role), mas a tabela `roles` é uma
referência espelhada no banco para manter integridade via FK e
permitir relatórios/joins sem precisar carregar o enum.

A tabela `user_role_assignment` é o coração: liga usuário -> papel -> escopo.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship

# Ajuste este import para o db do seu projeto.
# Exemplo típico Flask-SQLAlchemy:
#   from extensions import db
#   Base = db.Model
from extensions import db  # noqa: F401  (placeholder — ajustar no projeto real)


class RoleRef(db.Model):
    """Espelho em banco do enum Role. Populado pelo seed."""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    codigo = Column(String(50), unique=True, nullable=False, index=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(String(255))

    assignments = relationship("UserRoleAssignment", back_populates="role")

    def __repr__(self) -> str:
        return f"<RoleRef {self.codigo}>"


class UserRoleAssignment(db.Model):
    """
    Atribuição de papel a um usuário com escopo opcional.

    Exemplos:
      - user_id=10, role=APROVADOR, scope_type=UNIDADE, scope_id=3
        -> Fulano aprova registros da unidade 3
      - user_id=10, role=VISUALIZADOR, scope_type=GLOBAL, scope_id=None
        -> Fulano visualiza tudo
    """
    __tablename__ = "user_role_assignments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)

    scope_type = Column(String(20), nullable=False, default="global")
    scope_id = Column(Integer, nullable=True)  # id da unidade/tipo/etc; null = global

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    expires_at = Column(DateTime, nullable=True)  # atribuições temporárias

    role = relationship("RoleRef", back_populates="assignments")

    __table_args__ = (
        UniqueConstraint(
            "user_id", "role_id", "scope_type", "scope_id",
            name="uq_user_role_scope",
        ),
        Index("ix_assignment_user_scope", "user_id", "scope_type", "scope_id"),
    )

    def is_active(self) -> bool:
        if self.expires_at is None:
            return True
        return datetime.utcnow() < self.expires_at
