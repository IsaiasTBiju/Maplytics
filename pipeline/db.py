import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

def get_engine():
    """Returns a SQLAlchemy engine connected to the local PostGIS database."""
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    dbname = os.getenv("DB_NAME")

    url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    return create_engine(url)