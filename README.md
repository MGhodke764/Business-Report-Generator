# AI-Powered Business Report Generator

**Mini Project —**

A Streamlit application that analyses a sales CSV using Pandas, displays business KPIs and charts with Plotly, and uses Google Gemini to generate a written business report from aggregated statistics.

## Features
- Upload a sales CSV
- Calculate total revenue, order count, units sold and average order value
- Identify top products by revenue
- Analyse monthly revenue trends
- Display interactive Plotly charts
- Generate AI-written insights and recommendations with Gemini
- Download the generated report as a text file
- Download a sample CSV

## Required CSV columns
`date`, `product`, `quantity`, `unit_price`

Optional column: `order_id` (used to count unique orders). If it is not present, each valid row is counted as one order. An optional `revenue` column can be supplied; otherwise revenue is calculated as quantity × unit price.

## Run locally (Mac / Windows)
1. Install Python 3.10 or newer.
2. Open Terminal in this project folder.
3. Create and activate a virtual environment:

   **Mac**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

   **Windows**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

4. Install packages:
   ```bash
   pip install -r requirements.txt
   ```
5. Start the app:
   ```bash
   streamlit run app.py
   ```
6. Get a Gemini API key from https://aistudio.google.com/app/apikey and paste it in the app's sidebar.

## Important security note
Do not commit API keys, `.env` files, or `venv/` to GitHub. The app accepts the key in the password field for the current session. The raw CSV rows are processed locally; only aggregated statistics are sent to Gemini for report generation.

## Sample data
Use `sample_sales_data.csv` to test the application.

## Project workflow
CSV Upload → Pandas Analysis → Aggregated Metrics → Gemini LLM → AI Business Report + Plotly Charts.

## Limitations
- This is a mini-project demonstration using sample sales data.
- Revenue is not profit; cost, tax, returns and discounts are not included unless explicitly added to the dataset and implemented.
- AI-generated suggestions should be reviewed by a business user.
