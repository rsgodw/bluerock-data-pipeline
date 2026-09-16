import os
from diagrams import Diagram, Cluster, Edge
from diagrams.programming.language import Python
from diagrams.saas.analytics import Snowflake
from diagrams.onprem.analytics import Dbt, Powerbi

# Force Python to find the Graphviz binaries during execution
os.environ["PATH"] += os.pathsep + r"C:\Program Files\Graphviz\bin"
os.environ["PATH"] += os.pathsep + r"C:\Program Files (x86)\Graphviz\bin"

# Define the graph attributes for a clean, presentation-ready look
graph_attr = {
    "fontsize": "18",
    "pad": "0.5"
}

with Diagram("Bluerock Enterprise Data Pipeline", show=True, graph_attr=graph_attr, direction="LR"):
    
    # 1. Ingestion Layer
    ingest = Python("Faker Ingestion\n(ingest.py)")
    
    # 2. Snowflake Data Warehouse & dbt Transformations
    with Cluster("Snowflake Data Warehouse"):
        
        with Cluster("Landing Zone"):
            raw = Snowflake("RAW Schema\n(Untransformed Data)")
            
        with Cluster("dbt Transformation Layer"):
            staging = Dbt("ANALYTICS_STAGING\n(stg_accounts, stg_members, stg_transactions)")
            marts = Dbt("ANALYTICS Schema\n(FCT_TRANSACTIONS, DIM_DATE, etc.)")
            
    # 3. Consumer Endpoints
    with Cluster("Data Consumers"):
        pbi = Powerbi("Power BI\n(Import Mode / VertiPaq Engine)")
        ml = Python("Data Science\n(Isolation Forest Model)")

    # 4. Map the Data Flow (Edges)
    ingest >> Edge(label="Extract & Load", color="darkblue") >> raw
    raw >> Edge(label="Clean & Cast", color="darkgreen") >> staging
    staging >> Edge(label="Kimball Star Schema Join", color="darkgreen") >> marts
    
    # Dual output from the Marts layer
    marts >> Edge(label="Memory Import", color="purple") >> pbi
    marts >> Edge(label="Feature Engineering", color="firebrick") >> ml