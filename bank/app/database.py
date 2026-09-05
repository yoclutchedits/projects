
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

# --- Database URL ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./bank.db"

# --- Engine ---
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# --- Enforce foreign key constraints on every connection ---
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# --- Session factory ---
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Declarative base ---
Base = declarative_base()


# --- Dependency for FastAPI routes ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()