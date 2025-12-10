# Databricks notebook source
import yaml

with open("job_conf.yaml", "r") as f:
    job_conf = yaml.safe_load(f)

# COMMAND ----------

display(job_conf)

# COMMAND ----------

db_password = dbutils.secrets.get(scope=job_conf['db_password_scope'], key=job_conf['lakebase_db_password_key'])

# COMMAND ----------

database_url =  f"postgresql+psycopg://sanabil_app:{db_password}@{job_conf['lakebase_instance_host']}:5432/{job_conf['lakebase_db_name']}?sslmode=require"

# COMMAND ----------

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
engine = None
SessionLocal = None
def init_db_pool():
    global engine, SessionLocal
    try:
        database_url 
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            future=True
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        print("Database connection pool initialized successfully")
    except Exception as e:
        print(f"Failed to initialize database pool: {e}")
        raise

# COMMAND ----------

from contextlib import contextmanager
@contextmanager
def get_db_connection():
    if engine is None:
        init_db_pool()
    
    connection = engine.connect()
    try:
        yield connection
    finally:
        connection.close()

@contextmanager
def get_db_session():
    if SessionLocal is None:
        init_db_pool()
    
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    with get_db_connection() as conn:
        result = conn.execute(text(query), params or {})
        if fetch_one:
            row = result.mappings().first()
            return dict(row) if row else None
        elif fetch_all:
            return [dict(row) for row in result.mappings().all()]
        return result

def execute_commit_statement(statment, params=None):
    try:
        with get_db_connection() as conn:
            conn.execute(text(statment),params or {})
            conn.commit()    
    except Exception as e:
        print(f"Failed to execute the ddl query: {e}")
        raise