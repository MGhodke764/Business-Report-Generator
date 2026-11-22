import os
from io import StringIO
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
from google import genai

st.set_page_config(page_title="AI Business Report Generator", page_icon="📊", layout="wide")

st.markdown("""
<style>
    .main {background-color: #f7f9fc;}
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    div[data-testid="stMetric"] {
        background: white; padding: 18px; border-radius: 12px;
        border: 1px solid #e8edf5;
    }
    .report-card {
        background: white; padding: 22px; border-radius: 12px;
        border: 1px solid #e8edf5; line-height: 1.65;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 AI-Powered Business Report Generator")
st.caption("Upload sales data to explore performance and generate an AI-written business report.")

with st.sidebar:
    st.header("⚙️ Settings")
    st.write("**LLM provider:** Google Gemini")
    api_key = st.text_input(
        "Gemini API key",
        value=os.getenv("GEMINI_API_KEY", ""),
        type="password",
        help="Get a key from Google AI Studio. Your key is used only for this session."
    )
    model_name = st.text_input("Gemini model", value="gemini-3.8-flash")
    st.divider()
    st.caption("Privacy: the app calculates metrics locally and sends only aggregated sales statistics to Gemini, not the raw CSV rows.")

def money(value):
    return f"₹{value:,.2f}"

def clean_and_analyse(df):
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

    required = ["date", "product", "quantity", "unit_price"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            "Missing required columns: " + ", ".join(missing) +
            ". Required columns are date, product, quantity, unit_price."
        )

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["product"] = df["product"].astype(str).str.strip()
    df = df.dropna(subset=["date", "product", "quantity", "unit_price"])
    df = df[(df["quantity"] > 0) & (df["unit_price"] >= 0)]
    df = df[df["product"] != ""]

    if df.empty:
        raise ValueError("No valid sales rows found. Check dates, quantities and prices.")

    if "revenue" in df.columns:
        df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
        df["revenue"] = df["revenue"].fillna(df["quantity"] * df["unit_price"])
    else:
        df["revenue"] = df["quantity"] * df["unit_price"]

    total_revenue = float(df["revenue"].sum())
    total_units = int(df["quantity"].sum())
    order_count = int(df["order_id"].nunique()) if "order_id" in df.columns else int(len(df))
    avg_order_value = total_revenue / order_count if order_count else 0.0

    product_summary = (
        df.groupby("product", as_index=False)
          .agg(revenue=("revenue", "sum"), units_sold=("quantity", "sum"))
          .sort_values("revenue", ascending=False)
    )

    monthly = (
        df.assign(month=df["date"].dt.to_period("M").dt.to_timestamp())
          .groupby("month", as_index=False)["revenue"].sum()
          .sort_values("month")
    )
    monthly["month_label"] = monthly["month"].dt.strftime("%b %Y")
    if len(monthly) > 1:
        monthly["growth_pct"] = monthly["revenue"].pct_change() * 100
    else:
        monthly["growth_pct"] = 0.0

    metrics = {
        "total_revenue": round(total_revenue, 2),
        "total_orders": order_count,
        "total_units_sold": total_units,
        "average_order_value": round(avg_order_value, 2),
        "date_range": f"{df['date'].min().date()} to {df['date'].max().date()}",
        "number_of_products": int(df["product"].nunique()),
        "top_products": product_summary.head(5).round(2).to_dict(orient="records"),
        "monthly_revenue": [
            {
                "month": row["month_label"],
                "revenue": round(float(row["revenue"]), 2),
                "growth_pct": round(float(row["growth_pct"]), 2) if pd.notna(row["growth_pct"]) else None,
            }
            for _, row in monthly.iterrows()
        ],
    }
    return df, metrics, product_summary, monthly

def generate_ai_report(metrics, api_key, model_name):
    if not api_key:
        raise ValueError("Enter your Gemini API key in the left sidebar to generate the AI report.")

    client = genai.Client(api_key=api_key)
    prompt = f"""
You are a careful business analyst. Write a concise, professional sales performance report
based ONLY on the aggregated statistics below. Do not invent causes, targets, costs, profit,
customer demographics, or facts that are not provided. Clearly label interpretations as
observations and recommendations as suggestions. If there is not enough data to support
a conclusion, say so.

Use these headings:
1. Executive Summary
2. Key Performance Metrics
3. Product Performance
4. Monthly Sales Trend
5. Business Insights
6. Actionable Recommendations
7. Data Limitations

Include numbers from the data where relevant. Use clear language suitable for a small-business manager.
Aggregated sales statistics:
{metrics}
"""
    response = client.models.generate_content(model=model_name, contents=prompt)
    if not response.text:
        raise RuntimeError("Gemini returned an empty response. Please try again.")
    return response.text.strip()

sample = pd.DataFrame({
    "date": ["2026-01-05", "2026-01-12", "2026-02-03", "2026-02-15",
             "2026-03-02", "2026-03-18", "2026-04-04", "2026-04-20",
             "2026-05-08", "2026-05-22", "2026-06-10", "2026-06-25"],
    "order_id": ["O101", "O102", "O103", "O104", "O105", "O106",
                 "O107", "O108", "O109", "O110", "O111", "O112"],
    "product": ["Laptop", "Mouse", "Keyboard", "Laptop", "Monitor", "Mouse",
                "Keyboard", "Laptop", "Monitor", "Mouse", "Laptop", "Keyboard"],
    "quantity": [1, 3, 2, 1, 1, 4, 2, 1, 2, 3, 2, 1],
    "unit_price": [55000, 600, 1800, 55000, 12000, 600, 1800, 55000, 12000, 600, 55000, 1800]
})
sample_csv = sample.to_csv(index=False).encode("utf-8")

left, right = st.columns([3, 1])
with left:
    uploaded_file = st.file_uploader("Upload your sales CSV file", type=["csv"])
with right:
    st.download_button("⬇️ Download sample CSV", data=sample_csv,
                       file_name="sample_sales_data.csv", mime="text/csv", use_container_width=True)

if uploaded_file is None:
    st.info("No file uploaded yet. Upload your own CSV or download the sample CSV to try the dashboard.")
    st.subheader("Required CSV columns")
    st.code("date, product, quantity, unit_price\n2026-01-05, Laptop, 1, 55000", language="csv")
    st.stop()

try:
    raw_df = pd.read_csv(uploaded_file)
    sales_df, metrics, product_summary, monthly = clean_and_analyse(raw_df)
except Exception as exc:
    st.error(f"Could not process the CSV: {exc}")
    st.stop()

st.success(f"Successfully analysed {len(sales_df):,} valid sales rows.")
st.caption(f"Reporting period: {metrics['date_range']}")

st.subheader("Business overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Revenue", money(metrics["total_revenue"]))
c2.metric("Total Orders", f"{metrics['total_orders']:,}")
c3.metric("Units Sold", f"{metrics['total_units_sold']:,}")
c4.metric("Average Order Value", money(metrics["average_order_value"]))

st.divider()
st.subheader("Sales analytics")
chart1, chart2 = st.columns(2)
with chart1:
    st.markdown("**Monthly revenue trend**")
    fig_month = px.line(monthly, x="month", y="revenue", markers=True,
                        labels={"month": "Month", "revenue": "Revenue (₹)"})
    fig_month.update_layout(margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig_month, use_container_width=True)
with chart2:
    st.markdown("**Top 5 products by revenue**")
    top5 = product_summary.head(5).sort_values("revenue")
    fig_product = px.bar(top5, x="revenue", y="product", orientation="h",
                         labels={"revenue": "Revenue (₹)", "product": "Product"})
    fig_product.update_layout(margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig_product, use_container_width=True)

st.subheader("Product performance")
display_products = product_summary.copy()
display_products["revenue"] = display_products["revenue"].map(money)
st.dataframe(display_products, use_container_width=True, hide_index=True)

with st.expander("View cleaned sales data"):
    st.dataframe(sales_df, use_container_width=True, hide_index=True)

st.divider()
st.subheader("✨ AI-generated business report")
st.write("Gemini receives the calculated summary statistics, not the original transaction-level CSV.")
if st.button("Generate AI Business Report", type="primary", use_container_width=True):
    try:
        with st.spinner("Gemini is analysing the sales summary and writing your report..."):
            report = generate_ai_report(metrics, api_key, model_name)
        st.session_state["business_report"] = report
        st.session_state["report_metrics"] = metrics
    except Exception as exc:
        st.error(f"Report generation failed: {exc}")

if st.session_state.get("business_report"):
    st.markdown(st.session_state["business_report"])
    report_text = (
        "AI-POWERED BUSINESS REPORT\n"
        f"Generated: {datetime.now().strftime('%d %B %Y, %I:%M %p')}\n"
        f"Reporting period: {st.session_state['report_metrics']['date_range']}\n\n"
        + st.session_state["business_report"]
    )
    st.download_button("⬇️ Download business report (.txt)", data=report_text.encode("utf-8"),
                       file_name="business_report.txt", mime="text/plain")
else:
    st.caption("Click the button above after entering your Gemini API key to create the written report.")

st.caption("Academic mini project • Roll No. 70 • Business Report Generator")
