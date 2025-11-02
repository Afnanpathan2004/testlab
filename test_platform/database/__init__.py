"""Database connection management and session utilities."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base
from sqlalchemy.pool import NullPool, QueuePool

from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

Base = declarative_base()


@st.cache_resource
def get_engine() -> Engine:
    """Create SQLAlchemy engine with environment-appropriate pooling.

    Production: QueuePool(pool_size=10, max_overflow=20, pool_pre_ping=True, pool_recycle=3600)
    Development: NullPool
    """
    try:
        if settings.is_production:
            engine = create_engine(
                settings.database_url,
                echo=settings.database_echo,
                future=True,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
            )
        else:
            engine = create_engine(
                settings.database_url,
                echo=settings.database_echo,
                future=True,
                poolclass=NullPool,
            )
        logger.info("Database engine created")
        # Auto-create tables only in development to ease first run
        if settings.is_development:
            try:
                from . import models  # noqa: F401  # ensure model metadata is loaded
                Base.metadata.create_all(bind=engine)
                logger.info("Database tables ensured (development mode)")
            except Exception as ce:  # noqa: BLE001
                logger.error("Failed to create tables automatically: %s", ce)
        return engine
    except Exception as exc:
        logger.error("Failed to create database engine: %s", exc)
        raise


@st.cache_resource
def get_session_factory() -> sessionmaker[Session]:
    """Return a sessionmaker bound to the engine."""
    engine = get_engine()
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return factory


def get_db_session() -> Session:
    """Get a new database session. Caller is responsible for closing it."""
    factory = get_session_factory()
    return factory()
