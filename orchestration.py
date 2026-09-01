import os
import sys
import shutil
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from dagster import asset, AssetExecutionContext, Definitions
from dagster_dbt import DbtCliResource
from dagster_slack import make_slack_on_run_failure_sensor, SlackResource
import snowflake.connector

# Load environment variables from .env
load_dotenv()

# Resolve paths
BASE_DIR = Path(__file__).parent.resolve()
ANALYTICS_DIR = BASE_DIR / "analytics"
DBT_EXECUTABLE = shutil.which("dbt") or str(Path(sys.executable).parent / "dbt.exe")

# Configure dbt resource pointing to ./analytics
dbt_resource = DbtCliResource(
    project_dir=str(ANALYTICS_DIR),
    profiles_dir=str(ANALYTICS_DIR),
    dbt_executable=DBT_EXECUTABLE
)

# Configure Slack observability resource and failure sensor
slack_resource = SlackResource(token=os.getenv("SLACK_TOKEN", "dummy"))
slack_failure_sensor = make_slack_on_run_failure_sensor(
    channel="#data-pipeline-alerts",
    slack_token=os.getenv("SLACK_TOKEN", "dummy")
)


@asset
def ingest_raw_data(context: AssetExecutionContext):
    """Uses Python's subprocess to execute the existing ingest.py script."""
    context.log.info("Starting synthetic banking data ingestion via ingest.py...")
    script_path = BASE_DIR / "ingest.py"
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(BASE_DIR),
        check=True,
        capture_output=True,
        text=True
    )
    context.log.info(result.stdout)
    return "Raw data ingestion complete."


@asset(deps=[ingest_raw_data])
def apply_pii_classification(context: AssetExecutionContext):
    """Uses the Snowflake Python connector and credentials from .env to execute SYSTEM$CLASSIFY."""
    context.log.info("Connecting to Snowflake to execute automated PII classification...")
    load_dotenv()
    
    conn = snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        role=os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
        database=os.getenv("SNOWFLAKE_DATABASE", "CREDIT_UNION_DB"),
        schema="RAW"
    )
    try:
        with conn.cursor() as cur:
            cur.execute("CALL SYSTEM$CLASSIFY('CREDIT_UNION_DB.RAW.MEMBERS', {'auto_tag': true});")
            context.log.info("Successfully executed SYSTEM$CLASSIFY on CREDIT_UNION_DB.RAW.MEMBERS.")
    finally:
        conn.close()
        context.log.info("Snowflake connection closed.")
        
    return "PII classification applied."


@asset(deps=[apply_pii_classification])
def run_dbt_models(context: AssetExecutionContext, dbt: DbtCliResource):
    """Uses the dagster-dbt integration to run the dbt project located in ./analytics."""
    context.log.info("Executing dbt run in ./analytics...")
    load_dotenv()
    dbt_cli_invocation = dbt.cli(["run"])
    for event in dbt_cli_invocation.stream_raw_events():
        if isinstance(event, dict):
            msg = event.get("data", {}).get("msg")
            if msg:
                context.log.info(msg)
    return "dbt models run completed."


defs = Definitions(
    assets=[ingest_raw_data, apply_pii_classification, run_dbt_models],
    resources={
        "dbt": dbt_resource,
        "slack": slack_resource
    },
    sensors=[slack_failure_sensor]
)
