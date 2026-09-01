import os
import sys
import random
import logging
import pandas as pd
from faker import Faker
from dotenv import load_dotenv
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas

# Set seed for idempotency across Faker and random generators
Faker.seed(42)
random.seed(42)

# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ingest")


def generate_members(fake=None, num_records=100):
    """Generates synthetic member records with US cities and states."""
    if fake is None:
        fake = Faker()
    members = []
    for _ in range(num_records):
        has_phone = random.random() < 0.85
        phone = fake.phone_number() if has_phone else None
        join_date = fake.date_between(start_date="-5y", end_date="today")
        members.append({
            "MEMBER_ID": fake.uuid4(),
            "FIRST_NAME": fake.first_name(),
            "LAST_NAME": fake.last_name(),
            "EMAIL": fake.email(),
            "PHONE_NUMBER": phone,
            "HAS_PHONE_NUMBER": bool(has_phone),
            "CITY": fake.city(),
            "STATE": fake.state_abbr(),
            "JOIN_DATE": join_date.strftime("%Y-%m-%d")
        })
    return pd.DataFrame(members)


def generate_synthetic_data():
    """Generates synthetic banking data in 3NF (Members, Accounts, Transactions)."""
    fake = Faker()
    
    logger.info("Generating synthetic data using Faker (seed=42)...")
    
    # 1. Members: 100 records
    df_members = generate_members(fake, num_records=100)
    logger.info(f"Generated {len(df_members)} member records.")
    
    # 2. Accounts: 200 records
    member_ids = df_members["MEMBER_ID"].tolist()
    accounts = []
    for _ in range(200):
        accounts.append({
            "ACCOUNT_ID": fake.uuid4(),
            "MEMBER_ID": random.choice(member_ids),
            "ACCOUNT_TYPE": random.choice(["Checking", "Savings"]),
            "BALANCE": round(random.uniform(50.0, 50000.0), 2)
        })
    df_accounts = pd.DataFrame(accounts)
    logger.info(f"Generated {len(df_accounts)} account records.")
    
    # 3. Transactions: 1,000 records
    account_ids = df_accounts["ACCOUNT_ID"].tolist()
    transactions = []
    for _ in range(1000):
        tx_date = fake.date_time_between(start_date="-2y", end_date="now")
        transactions.append({
            "TRANSACTION_ID": fake.uuid4(),
            "ACCOUNT_ID": random.choice(account_ids),
            "TRANSACTION_DATE": tx_date.strftime("%Y-%m-%d %H:%M:%S"),
            "AMOUNT": round(random.uniform(1.0, 2500.0), 2),
            "TRANSACTION_TYPE": random.choice(["Deposit", "Withdrawal"])
        })
    df_transactions = pd.DataFrame(transactions)
    logger.info(f"Generated {len(df_transactions)} transaction records.")
    
    return df_members, df_accounts, df_transactions


def get_snowflake_connection():
    """Establishes connection to Snowflake using .env credentials."""
    load_dotenv()
    
    account = os.getenv("SNOWFLAKE_ACCOUNT")
    user = os.getenv("SNOWFLAKE_USER")
    password = os.getenv("SNOWFLAKE_PASSWORD")
    role = os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN")
    warehouse = os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
    database = os.getenv("SNOWFLAKE_DATABASE", "CREDIT_UNION_DB")
    schema = "RAW"
    
    logger.info(f"Connecting to Snowflake account '{account}' as user '{user}' (role='{role}', database='{database}', schema='{schema}')...")
    
    conn = snowflake.connector.connect(
        account=account,
        user=user,
        password=password,
        role=role,
        warehouse=warehouse,
        database=database,
        schema=schema
    )
    logger.info("Successfully connected to Snowflake.")
    return conn


def setup_and_truncate_tables(conn):
    """Ensures tables exist in RAW schema and truncates them for Nuke & Pave ingestion."""
    ddl_statements = [
        """
        CREATE TABLE IF NOT EXISTS CREDIT_UNION_DB.RAW.MEMBERS (
            MEMBER_ID VARCHAR(36) PRIMARY KEY,
            FIRST_NAME VARCHAR(100),
            LAST_NAME VARCHAR(100),
            EMAIL VARCHAR(255),
            PHONE_NUMBER VARCHAR(50),
            HAS_PHONE_NUMBER BOOLEAN,
            CITY VARCHAR,
            STATE VARCHAR,
            JOIN_DATE DATE
        );
        """,
        """
        ALTER TABLE IF EXISTS CREDIT_UNION_DB.RAW.MEMBERS ADD COLUMN IF NOT EXISTS CITY VARCHAR;
        """,
        """
        ALTER TABLE IF EXISTS CREDIT_UNION_DB.RAW.MEMBERS ADD COLUMN IF NOT EXISTS STATE VARCHAR;
        """,
        """
        CREATE TABLE IF NOT EXISTS CREDIT_UNION_DB.RAW.ACCOUNTS (
            ACCOUNT_ID VARCHAR(36) PRIMARY KEY,
            MEMBER_ID VARCHAR(36),
            ACCOUNT_TYPE VARCHAR(20),
            BALANCE FLOAT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS CREDIT_UNION_DB.RAW.TRANSACTIONS (
            TRANSACTION_ID VARCHAR(36) PRIMARY KEY,
            ACCOUNT_ID VARCHAR(36),
            TRANSACTION_DATE TIMESTAMP_NTZ,
            AMOUNT FLOAT,
            TRANSACTION_TYPE VARCHAR(20)
        );
        """
    ]
    
    truncate_statements = [
        "TRUNCATE TABLE IF EXISTS CREDIT_UNION_DB.RAW.TRANSACTIONS;",
        "TRUNCATE TABLE IF EXISTS CREDIT_UNION_DB.RAW.ACCOUNTS;",
        "TRUNCATE TABLE IF EXISTS CREDIT_UNION_DB.RAW.MEMBERS;"
    ]
    
    with conn.cursor() as cur:
        for ddl in ddl_statements:
            cur.execute(ddl)
        logger.info("Verified target tables exist in CREDIT_UNION_DB.RAW.")
        
        logger.info("Executing Nuke & Pave (TRUNCATE TABLE) on RAW schema tables...")
        for trunc in truncate_statements:
            cur.execute(trunc)
        logger.info("Truncation complete.")


def load_data():
    """Generates synthetic data and loads it into Snowflake RAW tables."""
    df_members, df_accounts, df_transactions = generate_synthetic_data()
    
    conn = get_snowflake_connection()
    try:
        setup_and_truncate_tables(conn)
        
        # Ingest MEMBERS
        logger.info(f"Ingesting {len(df_members)} rows into CREDIT_UNION_DB.RAW.MEMBERS...")
        success, nchunks, nrows, _ = write_pandas(
            conn=conn,
            df=df_members,
            table_name="MEMBERS",
            database="CREDIT_UNION_DB",
            schema="RAW",
            quote_identifiers=False
        )
        if not success:
            raise RuntimeError("Failed to load data into MEMBERS table.")
        logger.info(f"Successfully inserted {nrows} rows into CREDIT_UNION_DB.RAW.MEMBERS.")
        
        # Ingest ACCOUNTS
        logger.info(f"Ingesting {len(df_accounts)} rows into CREDIT_UNION_DB.RAW.ACCOUNTS...")
        success, nchunks, nrows, _ = write_pandas(
            conn=conn,
            df=df_accounts,
            table_name="ACCOUNTS",
            database="CREDIT_UNION_DB",
            schema="RAW",
            quote_identifiers=False
        )
        if not success:
            raise RuntimeError("Failed to load data into ACCOUNTS table.")
        logger.info(f"Successfully inserted {nrows} rows into CREDIT_UNION_DB.RAW.ACCOUNTS.")
        
        # Ingest TRANSACTIONS
        logger.info(f"Ingesting {len(df_transactions)} rows into CREDIT_UNION_DB.RAW.TRANSACTIONS...")
        success, nchunks, nrows, _ = write_pandas(
            conn=conn,
            df=df_transactions,
            table_name="TRANSACTIONS",
            database="CREDIT_UNION_DB",
            schema="RAW",
            quote_identifiers=False
        )
        if not success:
            raise RuntimeError("Failed to load data into TRANSACTIONS table.")
        logger.info(f"Successfully inserted {nrows} rows into CREDIT_UNION_DB.RAW.TRANSACTIONS.")
        
        logger.info("Synthetic banking data ingestion pipeline completed successfully.")
        
    finally:
        conn.close()
        logger.info("Snowflake connection closed.")


if __name__ == "__main__":
    load_data()
