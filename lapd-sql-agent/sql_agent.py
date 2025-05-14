import snowflake.connector
import os
import logging
from dotenv import load_dotenv
import keyring

# === LOGGING ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from environment variables."""
    load_dotenv()
    config = {
        "SNOWFLAKE_ACCOUNT": os.getenv("SNOWFLAKE_ACCOUNT"),
        "SNOWFLAKE_DATABASE": os.getenv("SNOWFLAKE_DATABASE"),
        "SNOWFLAKE_SCHEMA": os.getenv("SNOWFLAKE_SCHEMA"),
        "SNOWFLAKE_WAREHOUSE": os.getenv("SNOWFLAKE_WAREHOUSE"),
        "SNOWFLAKE_RAW_TABLE": os.getenv("SNOWFLAKE_RAW_TABLE"),
        "SNOWFLAKE_TEMP_TABLE": os.getenv("SNOWFLAKE_TEMP_TABLE"),
        "SNOWFLAKE_USER": keyring.get_password("snowflake", "user"),
        "SNOWFLAKE_PASSWORD": keyring.get_password("snowflake", "pwd")
    }
    logger.info("Configuration successfully loaded.")
    return config

def connect_snowflake():
    """Establishes a connection to Snowflake."""
    config = load_config()
    try:
        conn = snowflake.connector.connect(
            account=config['SNOWFLAKE_ACCOUNT'],
            user=config['SNOWFLAKE_USER'],
            password=config['SNOWFLAKE_PASSWORD'],
            warehouse=config['SNOWFLAKE_WAREHOUSE'],
            database=config['SNOWFLAKE_DATABASE'],
            schema=config['SNOWFLAKE_SCHEMA'],
        )
        logger.info("Successfully connected to Snowflake.")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to Snowflake: {e}")
        return None

if __name__ == "__main__":
    connect_snowflake()