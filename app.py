import streamlit as st
import pandas as pd
import plotly.express as px

# ===================== PWA INJECTION ======================
def inject_pwa():
    st.markdown("""
        <link rel="manifest" href="/manifest.json" />
        <script>
            if ('serviceWorker' in navigator) {
                window.addEventListener('load', () => {
                    navigator.serviceWorker.register("/service-worker.js");
                });
            }
        </script>
    """, unsafe_allow_html=True)


# ================= PAGE CONFIGURATION =================
st.set_page_config(page_title="AutoVizAI", layout="wide")

st.title("📊 AutoVizAI – Power BI Style Dashboard")
st.write("Upload a dataset, analyze it using dashboard pages, and export an interactive HTML report.")

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

# ================= FUNCTIONS =================
def detect_column_types(df):
    for col in df.select_dtypes(include="object").columns:
        try:
            converted = pd.to_datetime(df[col])
            if converted.notna().sum() / len(converted) > 0.7:
                df[col] = converted
        except:
            pass

    numeric = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
    categorical = df.select_dtypes(include=["object", "category"]).columns.tolist()
    datetime = df.select_dtypes(include=["datetime64[ns]"]).columns.tolist()

    return numeric, categorical, datetime


def apply_filters(df, numeric_cols, categorical_cols, datetime_cols):
    st.sidebar.header("🔎 Filters")
    filtered_df = df.copy()

    for col in categorical_cols:
        options = df[col].dropna().unique().tolist()
        selected = st.sidebar.multiselect(col, options, default=options)
        if selected:
            filtered_df = filtered_df[filtered_df[col].isin(selected)]

    for col in numeric_cols:
        min_val, max_val = float(df[col].min()), float(df[col].max())
        selected_range = st.sidebar.slider(col, min_val, max_val, (min_val, max_val))
        filtered_df = filtered_df[
            (filtered_df[col] >= selected_range[0]) &
            (filtered_df[col] <= selected_range[1])
        ]

    if datetime_cols:
        date_col = datetime_cols[0]
        min_date, max_date = df[date_col].min(), df[date_col].max()
        selected_dates = st.sidebar.date_input(
            f"{date_col} range", [min_date, max_date]
        )
        if len(selected_dates) == 2:
            filtered_df = filtered_df[
                (filtered_df[date_col] >= pd.to_datetime(selected_dates[0])) &
                (filtered_df[date_col] <= pd.to_datetime(selected_dates[1]))
            ]

    return filtered_df


def generate_ai_insights(df, numeric_cols, categorical_cols):
    insights = []
    insights.append(f"The dataset contains {df.shape[0]} rows and {df.shape[1]} columns.")

    missing = df.isnull().sum().sum()
    insights.append(
        f"{missing} missing values detected."
        if missing else "No missing values detected."
    )

    for col in numeric_cols[:3]:
        insights.append(
            f"{col}: mean={df[col].mean():.2f}, min={df[col].min()}, max={df[col].max()}."
        )

    for col in categorical_cols[:2]:
        insights.append(
            f"Most frequent value in '{col}' is '{df[col].value_counts().idxmax()}'"
        )

    return insights


def generate_html_report(df, numeric_cols, categorical_cols, datetime_cols, insights, figures):
    charts = "".join(figures)

    return f"""
    <html>
    <head>
        <title>AutoVizAI Report</title>
        <style>
            body {{ font-family: Arial; padding: 30px; }}
            h1, h2 {{ color: #2E86C1; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ccc; padding: 8px; }}
        </style>
    </head>
    <body>
        <h1>📊 AutoVizAI – Interactive Data Report</h1>

        <h2>Overview</h2>
        <p>Rows: {df.shape[0]} | Columns: {df.shape[1]} | Missing: {df.isnull().sum().sum()}</p>

        <h2>Dataset Understanding</h2>
        <ul>
            <li>Numeric: {", ".join(numeric_cols)}</li>
            <li>Categorical: {", ".join(categorical_cols)}</li>
            <li>Date: {", ".join(datetime_cols)}</li>
        </ul>

        <h2>Preview</h2>
        {df.head(10).to_html(index=False)}

        <h2>Statistics</h2>
        {df[numeric_cols].describe().T.to_html() if numeric_cols else "No numeric columns"}

        <h2>Insights</h2>
        <ul>{"".join([f"<li>{i}</li>" for i in insights])}</ul>

        <h2>Visual Analysis</h2>
        {charts}
    </body>
    </html>
    """

# ================= MAIN APP =================
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    numeric_cols, categorical_cols, datetime_cols = detect_column_types(df)
    filtered_df = apply_filters(df, numeric_cols, categorical_cols, datetime_cols)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["📄 Overview", "🧠 Understanding", "📊 Visuals", "🧠 Insights", "📥 Export"]
    )

    # -------- OVERVIEW --------
    with tab1:
        st.dataframe(filtered_df.head(), use_container_width=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Rows", filtered_df.shape[0])
        c2.metric("Columns", filtered_df.shape[1])
        c3.metric("Missing", filtered_df.isnull().sum().sum())

    # -------- UNDERSTANDING --------
    with tab2:
        st.write("Numeric Columns:", numeric_cols)
        st.write("Categorical Columns:", categorical_cols)
        st.write("Date Columns:", datetime_cols)
        if numeric_cols:
            st.dataframe(filtered_df[numeric_cols].describe().T)

    # -------- VISUALS --------
    figures = []
    with tab3:
        for col in numeric_cols:
            fig = px.histogram(filtered_df, x=col, title=f"{col} Distribution")
            st.plotly_chart(fig, use_container_width=True)
            figures.append(fig.to_html(full_html=False, include_plotlyjs="cdn"))

        for col in categorical_cols:
            vc = filtered_df[col].value_counts().head(10)
            fig = px.bar(x=vc.index, y=vc.values, title=f"{col} Categories")
            st.plotly_chart(fig, use_container_width=True)
            figures.append(fig.to_html(full_html=False, include_plotlyjs="cdn"))

    # -------- INSIGHTS --------
    with tab4:
        ai_insights = generate_ai_insights(filtered_df, numeric_cols, categorical_cols)
        for i in ai_insights:
            st.write("•", i)

    # -------- EXPORT --------
    with tab5:
        html_report = generate_html_report(
            filtered_df,
            numeric_cols,
            categorical_cols,
            datetime_cols,
            ai_insights,
            figures
        )

        st.download_button(
            "⬇️ Download Interactive HTML Report",
            html_report,
            "AutoVizAI_Report.html",
            "text/html"
        )
