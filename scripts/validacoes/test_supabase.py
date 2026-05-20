"""
Teste de conexão com Supabase via psycopg2.
Roda: python scripts/test_supabase.py
"""
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

conn_params = {
    "host": os.getenv("SUPABASE_HOST"),
    "port": os.getenv("SUPABASE_PORT"),
    "dbname": os.getenv("SUPABASE_DB"),
    "user": os.getenv("SUPABASE_USER"),
    "password": os.getenv("SUPABASE_PASSWORD"),
}

print(f"Conectando em {conn_params['host']}:{conn_params['port']}...")

try:
    conn = psycopg2.connect(**conn_params)
    cur = conn.cursor()
    cur.execute("SELECT version(), current_database(), current_user;")
    version, db, user = cur.fetchone()
    print(f"✅ Conectado!")
    print(f"   Database: {db}")
    print(f"   User: {user}")
    print(f"   Versão: {version[:50]}...")

    # Confirma que os schemas existem
    cur.execute("""
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name IN ('bronze', 'silver', 'gold')
        ORDER BY schema_name;
    """)
    schemas = [row[0] for row in cur.fetchall()]
    print(f"   Schemas encontrados: {schemas}")

    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ Erro de conexão: {e}")
