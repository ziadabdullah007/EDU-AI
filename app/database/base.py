"""
EduCore AI Platform — SQLAlchemy Declarative Base

Defines the shared Base class used by all ORM models.
Import Base from this module — never create it in individual model files.
"""

from sqlalchemy.orm import DeclarativeBase, MappedColumn


class Base(DeclarativeBase):
    """
    Shared declarative base for all SQLAlchemy models.

    All ORM models must inherit from this class to participate
    in the SQLAlchemy metadata registry.
    """

    pass
