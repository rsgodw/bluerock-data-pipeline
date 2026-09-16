import os
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
import snowflake.connector

def export_fct_transactions():
    load_dotenv()
    account = os.getenv("SNOWFLAKE_ACCOUNT")
    user = os.getenv("SNOWFLAKE_USER")
    password = os.getenv("SNOWFLAKE_PASSWORD")
    role = os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN")
    warehouse = os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
    database = os.getenv("SNOWFLAKE_DATABASE", "CREDIT_UNION_DB")
    
    print(f"Connecting to Snowflake {account}...")
    conn = snowflake.connector.connect(
        account=account,
        user=user,
        password=password,
        role=role,
        warehouse=warehouse,
        database=database,
        schema="ANALYTICS"
    )
    
    query = """
    SELECT 
        f.TRANSACTION_SK,
        f.TRANSACTION_ID,
        f.ACCOUNT_SK,
        f.ACCOUNT_ID,
        f.MEMBER_SK,
        f.MEMBER_ID,
        f.TRANSACTION_DATE_SK,
        f.TRANSACTION_DATE,
        f.TRANSACTION_TIMESTAMP,
        f.AMOUNT,
        f.TRANSACTION_TYPE,
        d.YEAR,
        d.MONTH,
        d.YEAR_MONTH,
        d.DAY_OF_WEEK,
        m.FIRST_NAME,
        m.LAST_NAME,
        m.CITY,
        m.STATE,
        a.ACCOUNT_TYPE,
        a.BALANCE as ACCOUNT_BALANCE
    FROM CREDIT_UNION_DB.ANALYTICS.FCT_TRANSACTIONS f
    LEFT JOIN CREDIT_UNION_DB.ANALYTICS.DIM_DATE d 
        ON f.TRANSACTION_DATE_SK = d.DATE_SK
    LEFT JOIN CREDIT_UNION_DB.ANALYTICS.DIM_MEMBERS m 
        ON f.MEMBER_SK = m.MEMBER_SK
    LEFT JOIN CREDIT_UNION_DB.ANALYTICS.DIM_ACCOUNTS a 
        ON f.ACCOUNT_SK = a.ACCOUNT_SK
    ORDER BY f.TRANSACTION_DATE ASC;
    """
    
    print("Executing query against ANALYTICS marts...")
    df = pd.read_sql(query, conn)
    conn.close()
    
    print(f"Extracted {len(df)} rows and {len(df.columns)} columns.")
    
    # Ensure data directory exists
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = data_dir / "fct_transactions.parquet"
    df.to_parquet(output_path, index=False, engine="pyarrow")
    print(f"Successfully saved Parquet dataset to {output_path.resolve()} (Size: {output_path.stat().st_size} bytes)")

if __name__ == "__main__":
    export_fct_transactions()
