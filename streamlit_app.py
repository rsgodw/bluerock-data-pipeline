import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# Page Configuration
st.set_page_config(
    page_title="Bluerock Financial Intelligence Dashboard",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Sleek Modern Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }
    .static-badge {
        background-color: #f0fdf4;
        border: 1px solid #86efac;
        color: #166534;
        padding: 0.6rem 1rem;
        border-radius: 8px;
        font-size: 0.9rem;
        margin-bottom: 1.5rem;
    }
    .kpi-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .kpi-title {
        font-size: 0.85rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0f172a;
        margin-top: 0.2rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    parquet_path = Path("data/fct_transactions.parquet")
    if not parquet_path.exists():
        st.error(f"Data file not found at {parquet_path.resolve()}. Please run export_parquet.py first.")
        st.stop()
    df = pd.read_parquet(parquet_path)
    df["TRANSACTION_DATE"] = pd.to_datetime(df["TRANSACTION_DATE"])
    df["YEAR_MONTH"] = df["YEAR_MONTH"].astype(str)
    return df


df = load_data()

# Header
st.markdown('<div class="main-header">💳 Bluerock Financial Intelligence Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Enterprise Banking Analytics • Kimball Dimensional Star Schema • Automated Data Governance</div>', unsafe_allow_html=True)

# Static Parquet Mode Callout
st.markdown("""
<div class="static-badge">
    ⚡ <strong>Public Portfolio Mode:</strong> This dashboard is powered by a high-performance static Parquet extract (<code>data/fct_transactions.parquet</code>) 
    exported directly from the Snowflake <strong>CREDIT_UNION_DB.ANALYTICS.FCT_TRANSACTIONS</strong> mart. This ensures instant sub-second response times and continuous public availability without requiring a running Snowflake compute warehouse.
</div>
""", unsafe_allow_html=True)

# Sidebar Filters
st.sidebar.header("🔍 Filter Analytics Mart")

# Year-Month Filter
all_months = sorted(df["YEAR_MONTH"].unique().tolist())
selected_months = st.sidebar.multiselect(
    "Select Year-Month",
    options=all_months,
    default=all_months
)

# Account Type Filter
all_acc_types = sorted(df["ACCOUNT_TYPE"].dropna().unique().tolist())
selected_acc_types = st.sidebar.multiselect(
    "Account Type",
    options=all_acc_types,
    default=all_acc_types
)

# Transaction Type Filter
all_tx_types = sorted(df["TRANSACTION_TYPE"].dropna().unique().tolist())
selected_tx_types = st.sidebar.multiselect(
    "Transaction Type",
    options=all_tx_types,
    default=all_tx_types
)

# State Filter
all_states = sorted(df["STATE"].dropna().unique().tolist())
selected_states = st.sidebar.multiselect(
    "Member State",
    options=all_states,
    default=all_states
)

# Apply Filters
filtered_df = df[
    (df["YEAR_MONTH"].isin(selected_months)) &
    (df["ACCOUNT_TYPE"].isin(selected_acc_types)) &
    (df["TRANSACTION_TYPE"].isin(selected_tx_types)) &
    (df["STATE"].isin(selected_states))
]

if filtered_df.empty:
    st.warning("No transactions match the selected filters. Please adjust your filter criteria.")
    st.stop()

# ----------------------------------------------------------------------
# Executive KPIs
# ----------------------------------------------------------------------
total_spend = filtered_df["AMOUNT"].sum()
avg_tx_value = filtered_df["AMOUNT"].mean()
total_txs = len(filtered_df)
anomalies_df = filtered_df[filtered_df["AMOUNT"] > 2000]
total_anomalies = len(anomalies_df)
unique_members = filtered_df["MEMBER_SK"].nunique()

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Total Spend</div>
        <div class="kpi-value">${total_spend:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Avg Transaction</div>
        <div class="kpi-value">${avg_tx_value:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Transactions</div>
        <div class="kpi-value">{total_txs:,}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Flagged Anomalies (> $2k)</div>
        <div class="kpi-value" style="color: #dc2626;">{total_anomalies:,}</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Active Members</div>
        <div class="kpi-value">{unique_members:,}</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# ----------------------------------------------------------------------
# Core Chart: Total Spend by YEAR_MONTH
# ----------------------------------------------------------------------
st.subheader("📈 Monthly Financial Trend: Total Spend by YEAR_MONTH")

monthly_summary = (
    filtered_df.groupby("YEAR_MONTH")
    .agg(
        TOTAL_SPEND=("AMOUNT", "sum"),
        AVG_SPEND=("AMOUNT", "mean"),
        TX_COUNT=("AMOUNT", "count")
    )
    .reset_index()
    .sort_values("YEAR_MONTH")
)

fig_monthly = go.Figure()

# Line chart for Total Spend
fig_monthly.add_trace(go.Scatter(
    x=monthly_summary["YEAR_MONTH"],
    y=monthly_summary["TOTAL_SPEND"],
    mode="lines+markers",
    name="Total Spend ($)",
    line=dict(color="#0284c7", width=3),
    marker=dict(size=8, color="#0369a1"),
    hovertemplate="<b>%{x}</b><br>Total Spend: $%{y:,.2f}<extra></extra>"
))

fig_monthly.update_layout(
    xaxis_title="Year-Month",
    yaxis_title="Total Transaction Spend ($)",
    template="plotly_white",
    hovermode="x unified",
    margin=dict(l=20, r=20, t=30, b=30),
    height=400,
    yaxis=dict(tickprefix="$", tickformat=",.0f")
)

st.plotly_chart(fig_monthly, use_container_width=True)

# ----------------------------------------------------------------------
# Secondary Visualizations: Breakdown & Geography
# ----------------------------------------------------------------------
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📊 Spend by Transaction & Account Type")
    breakdown_df = (
        filtered_df.groupby(["ACCOUNT_TYPE", "TRANSACTION_TYPE"])["AMOUNT"]
        .sum()
        .reset_index()
    )
    fig_breakdown = px.bar(
        breakdown_df,
        x="ACCOUNT_TYPE",
        y="AMOUNT",
        color="TRANSACTION_TYPE",
        barmode="group",
        color_discrete_map={"Deposit": "#10b981", "Withdrawal": "#f59e0b"},
        labels={"AMOUNT": "Total Amount ($)", "ACCOUNT_TYPE": "Account Type", "TRANSACTION_TYPE": "Type"}
    )
    fig_breakdown.update_layout(
        template="plotly_white",
        yaxis=dict(tickprefix="$", tickformat=",.0f"),
        height=340,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    st.plotly_chart(fig_breakdown, use_container_width=True)

with col_right:
    st.subheader("🗺️ Top Member States by Volume")
    state_df = (
        filtered_df.groupby("STATE")
        .agg(TOTAL_SPEND=("AMOUNT", "sum"), TX_COUNT=("AMOUNT", "count"))
        .reset_index()
        .sort_values("TOTAL_SPEND", ascending=False)
        .head(10)
    )
    fig_state = px.bar(
        state_df,
        x="TOTAL_SPEND",
        y="STATE",
        orientation="h",
        color="TOTAL_SPEND",
        color_continuous_scale="Blues",
        labels={"TOTAL_SPEND": "Total Spend ($)", "STATE": "State"}
    )
    fig_state.update_layout(
        template="plotly_white",
        yaxis=dict(autorange="reversed"),
        xaxis=dict(tickprefix="$", tickformat=",.0f"),
        coloraxis_showscale=False,
        height=340,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    st.plotly_chart(fig_state, use_container_width=True)

# ----------------------------------------------------------------------
# Anomaly & Transaction Explorer
# ----------------------------------------------------------------------
with st.expander("🚨 Flagged High-Value Transaction Anomalies (> $2,000)", expanded=False):
    st.dataframe(
        anomalies_df[[
            "TRANSACTION_ID", "TRANSACTION_DATE", "AMOUNT", 
            "TRANSACTION_TYPE", "ACCOUNT_TYPE", "CITY", "STATE"
        ]].sort_values("AMOUNT", ascending=False),
        use_container_width=True
    )

with st.expander("📋 View Sample Dimensional Mart Data", expanded=False):
    st.dataframe(filtered_df.head(100), use_container_width=True)
