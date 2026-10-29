import os
import psycopg2
import re
import json
from typing import TypedDict, Optional

from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from security_gate import is_sql_safe
from database_utils import extract_database_schema

# Load environment variables from .env
load_dotenv()

# Check required credentials
required_vars = [
    "GROQ_API_KEY",
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
    "DB_HOST",
    "DB_PORT"
]

# 1. Configuration
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
    max_retries=3
)

# PostgreSQL configuration
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT"))
}


# 2. Shared state
class State(TypedDict):
    question: str
    schema: str
    sql: Optional[str]
    result: Optional[str]
    error: Optional[str]
    attempts: int
    answer: Optional[str]


# 3. Generate SQL
def generate_sql(state: State):
    prompt = f"""
    You are an expert PostgreSQL analyst for FinAssist,
    a financial fraud detection and risk analysis system.

    TASK:
    Convert the user's question into one valid PostgreSQL query.

    DATABASE SCHEMA:
    {state['schema']}

    USER QUESTION:
    {state['question']}

    PREVIOUS ERROR:
    {state.get('error') or 'None'}

    RULES:
    1. Generate only one read-only SELECT query.
    2. Use only tables, columns, and relationships defined in the schema.
    3. Never invent column names, table names, or relationships.
    4. Use correct JOIN conditions based on the schema.
    5. Use appropriate WHERE, GROUP BY, ORDER BY, and aggregate
    functions when required.
    6. Use exact database values and data types in conditions.
    7. For counts, sums, averages, and other calculations,
    let PostgreSQL perform the calculations.
    8. Never generate INSERT, UPDATE, DELETE, DROP, ALTER,
    CREATE, TRUNCATE, or other data-modifying statements.
    9. Do not generate multiple SQL statements.
    10. If the previous query failed, correct it using the error
        message and the provided schema.
    11. If the question cannot be answered using the schema,
        do not invent a query.
    12. If user ask question which is not related to database, do not give suggestion.

    OUTPUT:
    Return only the SQL query.
    Do not include Markdown fences or explanations.
    """

    try:
        response = llm.invoke(prompt)
        sql = response.content.strip()

        # Remove Markdown code fences if present
        if sql.startswith("```"):
            sql = sql.split("\n", 1)[-1].removesuffix("```").strip()

        return {
            "sql": sql,
            "attempts": state["attempts"] + 1,
            "error": None
        }

    except Exception as e:
        return {
            "sql": None,
            "error": f"LLM error: {e}",
            "attempts": state["attempts"] + 1
        }


# 4. Validate and execute SQL
def execute_sql(state: State):
    sql = state.get("sql")

    if not sql:
        return {"result": None, "error": state.get("error", "No SQL generated")}

    if not is_sql_safe(sql):
        return {
            "result": None,
            "error": "SQL blocked by security validation"
        }

    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)

                columns = [col[0] for col in cur.description]
                rows = cur.fetchall()

                result = [dict(zip(columns, row)) for row in rows]
                result_string = json.dumps(result, default=str)

        return {"result": str(result_string), "error": None}

    except Exception as e:
        return {"result": None, "error": str(e)}


# 5. Generate final answer
def final_answer(state: State):
    if state.get("error"):
        return {"answer": f"Could not retrieve the data: {state['error']}"}


    prompt = f"""
    You are FinAssist, a financial data analysis assistant.

    USER QUESTION:
    {state['question']}

    DATABASE RESULTS:
    {state['result']}

    INSTRUCTIONS:
    1. Answer the user's question directly and clearly.
    2. Use only information supported by the database results.
    3. Do not invent values, transactions, customers, or risk scores.
    4. Preserve the exact numerical values returned by the database.
    5. Explain relevant findings in simple, professional language.
    6. Use bullet points when presenting multiple findings.
    7. If the results are empty, clearly state that no matching
    records were found.
    8. If the results are insufficient to answer the question,
    explain what information is missing.
    9. Do not claim that fraud occurred merely because a transaction
    has a high-risk score.
    10. Do not claim that a loan is approved, rejected, or defaulted
        unless the results explicitly support that conclusion.

    Return a concise, user-friendly answer.
    """


    try:
        response = llm.invoke(prompt)
        return {"answer": response.content}
    except Exception as e:
        return {"answer": f"Could not generate the answer: {e}"}


# 6. Decide whether to retry
def route(state: State):
    if state.get("error") and state["attempts"] < 3:
        return "generate_sql"

    return "final_answer"


# 7. Build the LangGraph workflow
graph = StateGraph(State)

graph.add_node("generate_sql", generate_sql)
graph.add_node("execute_sql", execute_sql)
graph.add_node("final_answer", final_answer)

graph.set_entry_point("generate_sql")
graph.add_edge("generate_sql", "execute_sql")

graph.add_conditional_edges(
    "execute_sql",
    route,
    {
        "generate_sql": "generate_sql",
        "final_answer": "final_answer"
    }
)

graph.add_edge("final_answer", END)

app = graph.compile()


# 8. Run the assistant
if __name__ == "__main__":
    state = {
        "question": "Run a risk assessment on applicant Saksham Bassi.",
        "schema": extract_database_schema(),
        "sql": None,
        "result": None,
        "error": None,
        "attempts": 0,
        "answer": None
    }

    response = app.invoke(state)
    print(response["answer"])
