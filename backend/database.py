import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# Local: sqlite:///./bitacora.db (por defecto, cero configuración)
# Producción: postgresql://usuario:password@host:5432/postgres  (Supabase)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bitacora.db")

# SQLite necesita este flag para funcionar bien con FastAPI (múltiples hilos).
# Postgres no lo necesita, así que solo se aplica condicionalmente.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependencia de FastAPI: entrega una sesión y la cierra siempre al final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
