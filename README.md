# 💳 Bluerock Financial Data Pipeline & Analytics Platform

[![dbt Slim CI Validation](https://github.com/rsgodw/bluerock-data-pipeline/actions/workflows/slim_ci.yml/badge.svg)](https://github.com/rsgodw/bluerock-data-pipeline/actions/workflows/slim_ci.yml)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://bluerock-data-pipeline.streamlit.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An enterprise-grade, modern data stack (MDS) financial data platform built for a credit union. This project showcases **end-to-end data engineering**: idempotent synthetic 3NF data generation, zero-touch dynamic PII masking governance, Kimball dimensional modeling in dbt, Dagster orchestration with Slack failure observability, automated GitHub Actions Slim CI, and public analytics dashboards powered by high-performance Parquet storage.

---

## 🚀 Live Interactive Demo

| Service | Link | Description |
| :--- | :--- | :--- |
| **Streamlit Analytics App** | [**Launch Live Dashboard ↗**](https://bluerock-data-pipeline.streamlit.app/) | Interactive executive dashboard featuring KPI cards, 'Total Spend by YEAR_MONTH' trendlines, and anomaly detection. |
| **Local Dashboard** | `streamlit run streamlit_app.py` | Run locally using the included high-performance Parquet snapshot. |

> [!NOTE]
> **Continuous Public Availability (Static Parquet Data Mode):**  
> To guarantee 24/7 public uptime and sub-second query performance without maintaining an active Snowflake compute warehouse, the live Streamlit application reads from a local columnar dataset (`data/fct_transactions.parquet`) extracted directly from the production `CREDIT_UNION_DB.ANALYTICS.FCT_TRANSACTIONS` dimensional mart.

---

## 🏗️ Architecture & Data Flow

```mermaid
flowchart TD
    classDef sourceStyle fill:#1e293b,stroke:#38bdf8,stroke-width:2px,color:#f8fafc;
    classDef rawStyle fill:#0f172a,stroke:#94a3b8,stroke-width:2px,color:#f8fafc;
    classDef stagingStyle fill:#1e1b4b,stroke:#818cf8,stroke-width:2px,color:#f8fafc;
    classDef martsStyle fill:#14532d,stroke:#4ade80,stroke-width:2px,color:#f8fafc;
    classDef consumerStyle fill:#701a75,stroke:#f472b6,stroke-width:2px,color:#f8fafc;
    classDef dateStyle fill:#365314,stroke:#a3e635,stroke-width:2px,color:#f8fafc;

    subgraph INGESTION ["1. Ingestion Layer"]
        ingest_script["Python Faker (ingest.py)<br/>• Idempotent Seed (42)<br/>• 3NF Relational Generation<br/>• Snowflake write_pandas & Truncate"]:::sourceStyle
    end

    subgraph RAW_ZONE ["2. Landing Zone (Snowflake RAW Schema)"]
        raw_members[("MEMBERS<br/>• Auto-Tagged PII")]:::rawStyle
        raw_accounts[("ACCOUNTS")]:::rawStyle
        raw_transactions[("TRANSACTIONS")]:::rawStyle
    end

    subgraph STAGING_ZONE ["3. Staging Layer (Snowflake ANALYTICS_STAGING Schema)"]
        stg_members["stg_members (View)<br/>• Column rename & Clean"]:::stagingStyle
        stg_accounts["stg_accounts (View)<br/>• Type normalization"]:::stagingStyle
        stg_transactions["stg_transactions (View)<br/>• ISO Timestamps"]:::stagingStyle
    end

    subgraph MARTS_ZONE ["4. Marts Layer (Snowflake ANALYTICS Schema)"]
        dim_members["DIM_MEMBERS (View)<br/>• Surrogate Key (member_sk)<br/>• Dynamic PII Masking"]:::martsStyle
        dim_accounts["DIM_ACCOUNTS (View)<br/>• Surrogate Key (account_sk)<br/>• Pure Kimball Link (member_sk)"]:::martsStyle
        dim_date["DIM_DATE (Table)<br/>• 10-Yr Snowflake Generator Spine<br/>• date_sk NUMBER(8,0)"]:::dateStyle
        fct_transactions["FCT_TRANSACTIONS (Table)<br/>• Temporal Split: DATE & TIMESTAMP<br/>• transaction_date_sk NUMBER(8,0)"]:::martsStyle
    end

    subgraph CONSUMER_ZONE ["5. Consumer & Analytics Layer"]
        power_bi["Power BI Semantic Model<br/>• TMDL Definition / PBIP<br/>• Import Mode (VertiPaq Engine)<br/>• DAX Business Measures"]:::consumerStyle
        streamlit_app["Streamlit Analytics Hub<br/>• Static Parquet Mode<br/>• Zero-Compute Cloud Host<br/>• Total Spend by Month"]:::consumerStyle
        data_science["Data Science ML Pipeline<br/>• Isolation Forest Anomaly Detection<br/>• Pure Timestamp Feature Extraction"]:::consumerStyle
    end

    ingest_script -->|Nuke & Pave Ingestion| raw_members
    ingest_script -->|Nuke & Pave Ingestion| raw_accounts
    ingest_script -->|Nuke & Pave Ingestion| raw_transactions

    raw_members -->|dbt source| stg_members
    raw_accounts -->|dbt source| stg_accounts
    raw_transactions -->|dbt source| stg_transactions

    stg_members -->|MD5 Surrogate Key| dim_members
    stg_accounts -->|Surrogate Join Key| dim_accounts
    stg_members -.->|Member SK Link| dim_accounts

    stg_transactions -->|Fact Transformation| fct_transactions
    stg_accounts -->|Enrich Account / Member SK| fct_transactions

    dim_members -->|1:N Star Join| fct_transactions
    dim_accounts -->|1:N Star Join| fct_transactions
    dim_date -->|1:N Date SK Join| fct_transactions

    MARTS_ZONE ==> power_bi
    MARTS_ZONE ==> streamlit_app
    MARTS_ZONE ==> data_science
```

---

## 🌟 Key Technical Highlights

### 1. Snowflake Foundational Infrastructure & RBAC
- **Least-Privilege Role Hierarchy:**
  - `DATA_ENGINEER`: Full administrative privileges across all schemas and execution warehouses.
  - `DATA_ANALYST`: Strictly scoped to analytical marts (`ANALYTICS`), with zero visibility into staging views or raw ingestion tables.
  - `DATA_SCIENTIST`: Scoped access across raw features and analytical marts for machine learning model development.
- **Strict Role Isolation:** Enforces `DEFAULT_SECONDARY_ROLES = ('NONE')` to prevent cross-role privilege escalation in web and BI interfaces.

### 2. Zero-Touch Automated PII Governance
- **Dynamic Masking Policies:** Configured column-level masking using Snowflake's native tag-based security.
- **Automated Discovery:** Integrates `CALL SYSTEM$CLASSIFY('CREDIT_UNION_DB.RAW.MEMBERS', {'auto_tag': true})` to discover, classify, and apply semantic category tags (`EMAIL`, `PHONE_NUMBER`) to PII columns at ingestion time without manual DDL tagging.

### 3. Kimball Dimensional Modeling in dbt
- **Deterministic Surrogate Keys:** Utilizes `dbt_utils.generate_surrogate_key` with MD5 hashes across all dimensions and fact tables.
- **Outrigger-Free Dimensional Hierarchy:** Links `dim_accounts` to `dim_members` via surrogate keys, strictly adhering to Kimball enterprise data warehouse design.
- **Temporal Datetime Split:**
  - `transaction_date` (`DATE`): Clean temporal join key for date aggregation.
  - `transaction_date_sk` (`NUMBER(8,0)`): Explicit 8-digit integer surrogate key (`YYYYMMDD`) preventing precision mismatches.
  - `transaction_timestamp` (`TIMESTAMP_NTZ`): High-precision timestamp preserved for machine learning and fraud anomaly detection.
- **Snowflake Date Dimension Generator:** Builds a 10-year continuous `dim_date` spine (`2020-01-01` to `2030`) using Snowflake's native `generator(rowcount => 3650)`.

### 4. Dagster Asset-Based Orchestration
- **Software-Defined Assets:** Structured DAG orchestrating `ingest_raw_data` $\rightarrow$ `apply_pii_classification` $\rightarrow$ `run_dbt_models`.
- **DbtCliResource Integration:** Streams execution events and metadata directly into Dagster event logs.
- **Slack Observability:** Features an automated run failure sensor (`make_slack_on_run_failure_sensor`) dispatching immediate alerting payloads to `#data-pipeline-alerts`.

### 5. Slim CI/CD with GitHub Actions
- **Continuous Validation:** [.github/workflows/slim_ci.yml](.github/workflows/slim_ci.yml) validates dbt dependencies, syntax, and schema tests on every pull request against `main`.
- **Automated Data Quality Testing:** Enforces unique keys, non-null constraints, accepted value enums (`Checking`, `Savings`), and custom singular business logic tests (`assert_positive_savings_balance.sql`).

---

## 📁 Repository Structure

```
bluerock-data-pipeline/
├── .github/workflows/
│   └── slim_ci.yml                  # GitHub Actions PR validation workflow
├── analytics/                       # dbt Transformation Project
│   ├── dbt_project.yml              # dbt configuration & custom schema routing
│   ├── packages.yml                 # dbt-utils package dependencies
│   ├── profiles.yml                 # Snowflake environment profile mappings
│   ├── models/
│   │   ├── staging/                 # 1:1 Cleaned Views (ANALYTICS_STAGING)
│   │   │   ├── sources.yml
│   │   │   ├── stg_accounts.sql
│   │   │   ├── stg_members.sql
│   │   │   └── stg_transactions.sql
│   │   └── marts/                   # Kimball Star Schema Marts (ANALYTICS)
│   │       ├── dim_accounts.sql
│   │       ├── dim_date.sql
│   │       ├── dim_members.sql
│   │       ├── fct_transactions.sql
│   │       └── schema.yml           # Model documentation & generic tests
│   └── tests/
│       └── assert_positive_savings_balance.sql # Singular business test
├── bluerock_dashboard.Report/       # Power BI PBIP Visual Layer
├── bluerock_dashboard.SemanticModel/# Power BI TMDL Semantic Model & DAX Measures
├── bluerock_dashboard.pbip          # Power BI Project File
├── data/
│   └── fct_transactions.parquet    # Local Parquet analytical snapshot
├── export_parquet.py                # Snowflake Mart to Parquet extraction script
├── flowchart.py                     # Diagrams-as-Code architecture generator
├── ingest.py                        # Faker 3NF synthetic data ingestion script
├── orchestration.py                 # Dagster Software-Defined Assets & Slack Sensor
├── setup_infrastructure.sql         # Snowflake Database, Schemas, Warehouses & RBAC
├── setup_governance.sql             # Snowflake Dynamic Masking & Tagging Setup
├── streamlit_app.py                 # Standalone Public Streamlit Dashboard
└── README.md
```

---

## 🛠️ Quickstart Guide

### Prerequisites
- Python 3.10+
- Snowflake Account with `ACCOUNTADMIN` role
- dbt-snowflake (`1.11+`)
- Dagster (`1.8+`)

### 1. Environment Configuration
Create a `.env` file in the project root:

```ini
SNOWFLAKE_ACCOUNT="your-snowflake-account"
SNOWFLAKE_USER="your-username"
SNOWFLAKE_PASSWORD="your-password"
SNOWFLAKE_ROLE="ACCOUNTADMIN"
SNOWFLAKE_WAREHOUSE="COMPUTE_WH"
SNOWFLAKE_DATABASE="CREDIT_UNION_DB"
SLACK_TOKEN="xoxb-your-slack-bot-token"
```

### 2. Infrastructure Setup
Execute foundational DDL in Snowflake:

```powershell
snow sql -f setup_infrastructure.sql
snow sql -f setup_governance.sql
```

### 3. Run Pipeline via Dagster
Launch Dagster to run the full ingestion and dbt pipeline:

```powershell
dagster dev -f orchestration.py
```
Open **[http://127.0.0.1:3000](http://127.0.0.1:3000)** and click **"Materialize all"**.

### 4. Launch Local Streamlit Dashboard
```powershell
streamlit run streamlit_app.py
```

---

## 👤 Author

**[Rodney Godwin](https://www.linkedin.com/in/rodneygodwin/)**  
- LinkedIn: [linkedin.com/in/rodneygodwin](https://www.linkedin.com/in/rodneygodwin/)  
- GitHub: [@rsgodw](https://github.com/rsgodw)  
- Repository: [bluerock-data-pipeline](https://github.com/rsgodw/bluerock-data-pipeline)

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
