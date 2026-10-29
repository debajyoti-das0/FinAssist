import os
import psycopg2
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()
required_vars = [
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
    "DB_HOST",
    "DB_PORT"
]

# Database connection parameters
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT"))
}

def extract_database_schema():
    """Extracts tables, columns, and foreign keys from PostgreSQL and formats for an LLM."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # 1. Extract Tables, Columns, and Data Types
        # We filter by table_schema = 'public' to ignore internal Postgres system tables.
        cur.execute("""
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position;
        """)
        columns_data = cur.fetchall()

        # 2. Extract Foreign Key Relationships
        cur.execute("""
            SELECT
                tc.table_name AS source_table,
                kcu.column_name AS source_column,
                ccu.table_name AS target_table,
                ccu.column_name AS target_column
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu
              ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY' 
              AND tc.table_schema = 'public';
        """)
        fks_data = cur.fetchall()

        # 3. Organize the data into a dictionary
        schema = defaultdict(list)
        for table_name, column_name, data_type in columns_data:
            schema[table_name].append(f"{column_name} ({data_type})")

        # 4. Format the output string for the LLM Prompt
        prompt_context = "### DATABASE SCHEMA ###\n\n"
        
        for table, columns in schema.items():
            prompt_context += f"Table: {table}\n"
            prompt_context += "Columns:\n"
            for col in columns:
                prompt_context += f"  - {col}\n"
            prompt_context += "\n"

        if fks_data:
            prompt_context += "### FOREIGN KEYS ###\n"
            for src_table, src_col, tgt_table, tgt_col in fks_data:
                prompt_context += f"- {src_table}.{src_col} references {tgt_table}.{tgt_col}\n"

        return prompt_context

    except Exception as e:
        print(f"Error extracting schema: {e}")
        return None
    finally:
        if cur: cur.close()
        if conn: conn.close()

# Execute and print the LLM context
if __name__ == "__main__":
    llm_schema_context = extract_database_schema()
    print(llm_schema_context)