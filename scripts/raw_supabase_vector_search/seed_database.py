# -*- coding: utf-8 -*-
"""
Siembra de datos de prueba en la tabla 'documents' de Supabase:
1. Genera los embeddings de 1536 dimensiones para 'Tesla Model 3' y 'iPhone 15 Pro'.
2. Los inserta en PostgreSQL usando psycopg y DATABASE_URL.
3. Ejecuta una búsqueda de prueba con 'electric vehicle' usando el operador <=> para verificar el Top Match.
"""

import os
import psycopg
from dotenv import load_dotenv
from openai import OpenAI

# Cargar el .env de la carpeta de demo
load_dotenv(r"C:\Users\mapog\Documents\supabase_vector_demo\.env")

client = OpenAI()
db_url = os.getenv("DATABASE_URL")
if not db_url:
    raise ValueError("Falta DATABASE_URL en .env")

DOCUMENTOS = [
    "Tesla Model 3",
    "iPhone 15 Pro",
]

print("1. Generando embeddings con text-embedding-3-small...")
datos_insertar = []
for doc in DOCUMENTOS:
    emb = client.embeddings.create(
        input=doc,
        model="text-embedding-3-small"
    ).data[0].embedding
    datos_insertar.append((doc, str(emb)))
    print(f"  - Generado embedding para: {doc}")

print("\n2. Insertando registros en la tabla 'documents' de Supabase...")
with psycopg.connect(db_url) as conn:
    with conn.cursor() as cur:
        # Limpiar tabla previa si existieran pruebas
        cur.execute("TRUNCATE TABLE documents;")
        for titulo, vector_str in datos_insertar:
            cur.execute(
                "INSERT INTO documents (title, embedding) VALUES (%s, %s::vector);",
                (titulo, vector_str)
            )
    conn.commit()

print(f"  [OK] {len(datos_insertar)} documentos insertados con éxito.")

# 3. Test de validación con 'electric vehicle'
print("\n3. Verificando búsqueda vectorial de prueba ('electric vehicle')...")
query_test = "electric vehicle"
q_emb = client.embeddings.create(
    input=query_test,
    model="text-embedding-3-small"
).data[0].embedding

with psycopg.connect(db_url) as conn:
    row = conn.execute(
        "SELECT title, embedding <=> %s::vector AS distancia FROM documents ORDER BY distancia LIMIT 1;",
        (str(q_emb),)
    ).fetchone()
    print(f"\n=======================================================")
    print(f" Consulta: '{query_test}'")
    print(f" Top Match: {row[0]} (Distancia coseno: {row[1]:.4f})")
    print(f"=======================================================")
