
import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        connect_timeout=5,
    )

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT current_database(), current_user, version();")
            result = cursor.fetchone()

            print(f"Banco: {result[0]}")
            print(f"Usuário: {result[1]}")
            print(f"Versão: {result[2]}")
    finally:
        conn.close()

if __name__ == "__main__":
    test_connection()
