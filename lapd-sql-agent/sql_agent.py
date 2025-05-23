"""
SQL Agent for LAPD Crime Data Exploration
This script provides a robust and modular solution for querying LAPD crime data
stored in a Snowflake database using natural language. It leverages the power of
Google's Gemini language model to translate user questions into optimized SQL
queries and then presents the results in a human-readable format.
"""
import os
import logging
import keyring
import snowflake.connector
from dotenv import load_dotenv
import google.generativeai as genai
from typing import List, Dict, Optional, Tuple
import re

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

def load_config() -> Dict[str, Optional[str]]:
    """Loads configuration from environment variables and keyring."""
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))
    config = {
        "SNOWFLAKE_ACCOUNT": os.getenv("SNOWFLAKE_ACCOUNT"),
        "SNOWFLAKE_DATABASE": os.getenv("SNOWFLAKE_DATABASE"),
        "SNOWFLAKE_SCHEMA": os.getenv("SNOWFLAKE_SCHEMA"),
        "SNOWFLAKE_WAREHOUSE": os.getenv("SNOWFLAKE_WAREHOUSE"),
        "SNOWFLAKE_USER": keyring.get_password("snowflake", "user"),
        "SNOWFLAKE_PASSWORD": keyring.get_password("snowflake", "pwd"),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
    }
    logger.info("Configuration loaded successfully.")
    return config

def connect_snowflake(config: Dict[str, Optional[str]]) -> Optional[snowflake.connector.SnowflakeConnection]:
    """Connects to Snowflake."""
    try:
        conn = snowflake.connector.connect(
            account=config["SNOWFLAKE_ACCOUNT"],
            user=config["SNOWFLAKE_USER"],
            password=config["SNOWFLAKE_PASSWORD"],
            warehouse=config["SNOWFLAKE_WAREHOUSE"],
            database=config["SNOWFLAKE_DATABASE"],
            schema=config["SNOWFLAKE_SCHEMA"],
        )
        logger.info("Connected to Snowflake.")
        return conn
    except Exception as e:
        logger.error(f"Snowflake connection failed: {e}")
        return None

def setup_gemini(api_key: str) -> Optional[genai.GenerativeModel]:
    """Sets up the Gemini GenerativeModel."""
    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(model_name="gemini-1.5-flash-latest")
    except Exception as e:
        logger.error(f"Gemini setup failed: {e}")
        return None

def load_schema_from_snowflake(conn, database: str, schema: str) -> Dict[str, List[Dict[str, str]]]:
    """Dynamically fetches schema information from Snowflake."""
    query = f"""
    SELECT
        TABLE_NAME,
        COLUMN_NAME,
        DATA_TYPE
    FROM {database}.INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = '{schema}'
    ORDER BY TABLE_NAME, ORDINAL_POSITION
    """
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()

        schema_dict = {}
        for table_name, column_name, data_type in rows:
            if table_name not in schema_dict:
                schema_dict[table_name] = []
            schema_dict[table_name].append({
                "COLUMN_NAME": column_name,
                "DATA_TYPE": data_type
            })
        logger.info("Schema loaded dynamically from Snowflake.")
        return schema_dict

    except Exception as e:
        logger.error(f"Failed to load schema from Snowflake: {e}")
        return {}

def generate_sql(model: genai.GenerativeModel, user_question: str, table_schemas: Dict[str, List[Dict[str, str]]]) -> Optional[str]:
    """Generates SQL queries with schema awareness."""

    def format_column(column: Dict[str, str]) -> str:
        """Formats a single column definition."""
        return f"{column['COLUMN_NAME']} ({column['DATA_TYPE']})"

    def format_table_schema(table: str, columns: List[Dict[str, str]]) -> str:
        """Formats the schema for a single table."""
        column_strings = [format_column(col) for col in columns]
        return f"{table}: {', '.join(column_strings)}"

    schema_text_lines = [
        format_table_schema(table, columns) for table, columns in table_schemas.items()
    ]
    schema_text = "\n".join(schema_text_lines)
    SYSTEM_PROMPT = f"""You are a Snowflake SQL expert. Generate optimized, correct SQL queries based on the provided Snowflake schema.

Schema:
{schema_text}

Instructions:
- Only generate SELECT queries.
- Always use the tables from the MART_CORE schema.
- Include only the necessary columns in the SELECT statement.
- Use table aliases to avoid ambiguity (e.g., table1 AS t1).
- Use JOINs to combine data from multiple tables when necessary.
- Apply WHERE filters to retrieve only relevant data.
- If the user asks for aggregated data (e.g., "count", "total", "average"), use GROUP BY and appropriate aggregate functions (e.g., COUNT, SUM, AVG).
- When using aggregate functions, provide a meaningful alias for the resulting column (e.g., COUNT(*) AS total_count).
- If the user asks for top N or bottom N results, use ORDER BY and LIMIT.
- Assume the main table for crime events is MART_CORE.FCT_CRIME_EVENTS (alias: f).
- Crucially, the table MART_CORE.DIM_AREA (alias: a) has columns ID and NAME. Use the NAME column to get area names.
- Respond with SQL only, do not include any other text.
- **CRITICAL: You MUST ONLY return the SQL query. Do not include any introductory phrases, explanations, or any other text before or after the SQL query.  The ENTIRE response should be a valid SQL query that can be executed directly by Snowflake.**

Example 1:
User Question: "How many crimes occurred in each area?"
SQL: SELECT a.NAME, COUNT(f.DR_NO) AS crime_count FROM MART_CORE.FCT_CRIME_EVENTS AS f JOIN MART_CORE.DIM_AREA AS a ON f.AREA_DIM_ID = a.ID GROUP BY a.NAME

Example 2:
User Question: "List the ages and DESCENT of the 10 oldest victims."
SQL: SELECT v.AGE, v.DESCENT FROM MART_CORE.DIM_VICTIM AS v WHERE v.DESCENT is NOT NULL ORDER BY v.AGE DESC LIMIT 10;

Example 3:
User Question: "What are the top 5 crime types?"
SQL: SELECT dc.DESCRIPTION, COUNT(*) AS crime_count FROM MART_CORE.FCT_CRIME_EVENTS AS f JOIN MART_CORE.BRIDGE_CRIME_CODE AS bcc ON f.DR_NO = bcc.DR_NO JOIN MART_CORE.DIM_CRIME_CODE AS dc ON bcc.CRIME_CODE_DIM_ID = dc.ID GROUP BY dc.DESCRIPTION ORDER BY crime_count DESC LIMIT 5;

Example 4:
User Question: "List the area names with the most crimes."
SQL: SELECT a.NAME, COUNT(f.DR_NO) AS crime_count FROM MART_CORE.FCT_CRIME_EVENTS AS f JOIN MART_CORE.DIM_AREA AS a ON f.AREA_DIM_ID = a.ID GROUP BY a.NAME ORDER BY crime_count DESC;
"""
    prompt = f"{SYSTEM_PROMPT}\n\nQuestion: {user_question}\nSQL:"
    try:
        response = model.generate_content(prompt)
        sql = response.text.strip().strip("```sql").strip("```")
        logger.info(f"Generated SQL:\n{sql}")
        return sql
    except Exception as e:
        logger.error(f"Gemini SQL generation failed: {e}")
        return None

def run_query(conn: snowflake.connector.SnowflakeConnection, sql: str) -> Tuple[List[str], List[tuple]]:
    """Executes the SQL query on Snowflake."""
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        cursor.close()
        return columns, rows
    except snowflake.connector.errors.ProgrammingError as e:
        logger.error(f"Snowflake Programming Error: {e} - SQL: {sql}")
        return [], []
    except snowflake.connector.errors.DatabaseError as e:
        logger.error(f"Snowflake Database Error: {e} - SQL: {sql}")
        return [], []
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        return [], []

def answer_question(question: str) -> str:
    """Answers the user's question using Gemini and the dynamically loaded schema."""
    config = load_config()
    conn = connect_snowflake(config)
    if not conn:
        return "Snowflake connection error."

    model = setup_gemini(config["GEMINI_API_KEY"])
    if not model:
        return "Gemini setup error."

    table_schemas = load_schema_from_snowflake(conn, config["SNOWFLAKE_DATABASE"], "MART_CORE")
    sql = generate_sql(model, question, table_schemas)
    if not sql or not sql.strip().lower().startswith("select"):
        return f"Invalid or no SQL generated: {sql}"
    sql = re.sub(r"^```(?:sql)?\s*|```$", "", sql.strip(), flags=re.IGNORECASE).strip()
    sql = ' '.join(sql.split())
    logger.info(f"LLM Generated SQL (before execution):\n{sql}")
    columns, rows = run_query(conn, sql)
    if not rows:
        return "No results found or error executing query."

    def truncate(value, length=100):
        return value if len(str(value)) <= length else str(value)[:length] + "..."

    MAX_ROWS = 10
    sample_rows = [
        [truncate(col) for col in row]
        for row in rows[:MAX_ROWS]
    ]
    results_string = "\n".join([", ".join(map(str, row)) for row in sample_rows])

    columns_string = ", ".join(columns)
    llm_prompt = f"""You are a helpful AI assistant that can understand SQL query results and provide natural language answers to the user's questions.
    User's Question: {question}
    SQL Query:
    {sql}
    Results:
    Columns: {columns_string}
    Data:\n{results_string}
    Based on the SQL query and its results, provide a concise and natural language answer to the user's question."""
    try:
        response = model.generate_content(llm_prompt)
        natural_language_answer = response.text.strip()
        logger.info(f"Natural language answer generated: {natural_language_answer}")
        return natural_language_answer
    except Exception as e:
        logger.error(f"Natural language answer generation failed: {e}")
        return f"Error generating natural language answer: {e}"

if __name__ == "__main__":
    while True:
        try:
            question = input("\nAsk a question about LAPD crime data (or type 'exit'): ")
            if question.lower() == "exit":
                break
            answer = answer_question(question)
            print(answer)
        except KeyboardInterrupt:
            break