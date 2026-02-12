import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
import streamlit as st
import logging

# -------------------------------
# CONFIG & LOGGING
# -------------------------------
st.set_page_config(page_title="Climate Data Analysis", layout="wide")

logging.basicConfig(
    filename='climate_analysis.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# -------------------------------
# LOAD & PREPROCESS DATA
# -------------------------------
@st.cache_data
def load_and_preprocess_data(uploaded_file):
    df = pd.read_csv(uploaded_file)

    if "Year" in df.columns:
        df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    if "Value" in df.columns:
        df["Value"] = pd.to_numeric(df["Value"], errors="coerce")

    df = df.dropna(subset=["Year", "Value"])
    return df

# -------------------------------
# DATA SUMMARY
# -------------------------------
def dataset_summary(df):
    st.subheader("Dataset Summary")
    st.dataframe(df.describe(include="all"))

    st.subheader("Columns")
    st.write(df.columns.tolist())

    if "Indicator" in df.columns:
        st.subheader("Indicators")
        st.write(df["Indicator"].unique())

    if "Country" in df.columns:
        st.subheader("Countries")
        st.write(df["Country"].unique())


    # ✅ ADDITION: Mean of every indicator
    if "Indicator" in df.columns and "Value" in df.columns:
        st.subheader("Mean Value of Each Indicator")

        mean_indicator = (
            df.groupby("Indicator")["Value"]
            .mean()
            .reset_index()
            .rename(columns={"Value": "Mean Value"})
        )

        st.dataframe(mean_indicator)

# -------------------------------
# VISUALIZATIONS
# -------------------------------
def plot_pie_clean(df):
    if "Indicator" not in df.columns:
        st.error("Indicator column missing")
        return

    indicator_counts = df["Indicator"].value_counts()

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.pie(indicator_counts.values, startangle=140)
    ax.legend(
        indicator_counts.index,
        title="Indicators",
        loc="center left",
        bbox_to_anchor=(1, 0.5)
    )
    ax.set_title("Distribution of Climate Indicators")
    st.pyplot(fig)

def plot_time_series(df, indicator_filter):
    if indicator_filter != "All":
        df = df[df["Indicator"] == indicator_filter]

    # ✅ Mean-based graphical time series
    ts_data = (
        df.groupby(["Year", "Indicator"])["Value"]
        .mean()
        .reset_index()
        .sort_values("Year")
    )

    fig = px.line(
        ts_data,
        x="Year",
        y="Value",
        color="Indicator",
        markers=True,
        title="Year-wise Mean Time Series Analysis"
    )

    fig.update_layout(
        xaxis_title="Year",
        yaxis_title="Mean Value"
    )

    st.plotly_chart(fig, use_container_width=True)

def plot_bar_top_countries(df, top_n):
    if "Country" not in df.columns:
        st.error("Country column missing")
        return

    top_countries = (
        df.groupby("Country")["Value"]
        .sum()
        .nlargest(top_n)
        .reset_index()
    )

    fig = px.bar(
        top_countries,
        x="Country",
        y="Value",
        title=f"Top {top_n} Countries by Value"
    )
    st.plotly_chart(fig, use_container_width=True)

def plot_correlation_heatmap(df):
    numeric_df = df.select_dtypes(include=["int64", "float64"])

    if numeric_df.shape[1] < 2:
        st.warning("Not enough numeric columns for correlation")
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(numeric_df.corr(), annot=True, cmap="coolwarm", ax=ax)
    ax.set_title("Correlation Heatmap")
    st.pyplot(fig)

# -------------------------------
# TREND ANALYSIS
# -------------------------------
def analyze_trends(df, indicator_filter):
    if indicator_filter != "All":
        df = df[df["Indicator"] == indicator_filter]

    df = df.sort_values("Year")

    X = df["Year"].values.reshape(-1, 1)
    y = df["Value"].values

    model = LinearRegression()
    model.fit(X, y)

    slope = model.coef_[0]
    r2 = model.score(X, y)

    st.subheader("Trend Analysis (Selected Indicator)")
    st.write(f"**Slope:** {slope:.4f}")
    st.write(f"**R² Score:** {r2:.4f}")

def plot_scatter_trends(df, indicator_filter):
    if indicator_filter == "All":
        st.warning("Select a specific indicator for line trend analysis.")
        return

    df = df[df["Indicator"] == indicator_filter]
    df = df.sort_values("Year")

    X = df["Year"].values.reshape(-1, 1)
    y = df["Value"].values

    model = LinearRegression()
    model.fit(X, y)
    y_pred = model.predict(X)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["Year"],
        y=df["Value"],
        mode="markers",
        name="Observed Data"
    ))

    fig.add_trace(go.Scatter(
        x=df["Year"],
        y=y_pred,
        mode="lines",
        name="Trend Line",
        line=dict(color="red", width=3)
    ))

    fig.update_layout(
        title=f"Trend Analysis – {indicator_filter}",
        xaxis_title="Year",
        yaxis_title="Value"
    )

    st.plotly_chart(fig, use_container_width=True)

# ✅ ADDITION: SLOPE SCATTER FOR ALL INDICATORS
def plot_indicator_slope_scatter(df):
    slope_data = []

    for indicator in df["Indicator"].unique():
        temp_df = df[df["Indicator"] == indicator]

        mean_df = (
            temp_df.groupby("Year")["Value"]
            .mean()
            .reset_index()
            .sort_values("Year")
        )

        if len(mean_df) < 2:
            continue

        X = mean_df["Year"].values.reshape(-1, 1)
        y = mean_df["Value"].values

        model = LinearRegression()
        model.fit(X, y)

        slope_data.append({
            "Indicator": indicator,
            "Slope": model.coef_[0]
        })

    slope_df = pd.DataFrame(slope_data)

    st.subheader("Indicator-wise Trend Slope Comparison")

    fig = px.scatter(
        slope_df,
        x="Indicator",
        y="Slope",
        size=abs(slope_df["Slope"]),
        color="Slope",
        title="Scatter Plot of Trend Slopes"
    )

    st.plotly_chart(fig, use_container_width=True)

# -------------------------------
# EXPORT
# -------------------------------
def export_filtered_data(df, indicator_filter):
    if indicator_filter != "All":
        df = df[df["Indicator"] == indicator_filter]

    csv = df.to_csv(index=False)

    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="filtered_climate_data.csv",
        mime="text/csv"
    )

# -------------------------------
# MAIN APP
# -------------------------------
def main():
    st.title("🌍 Climate Data Analysis Dashboard")

    uploaded_file = st.sidebar.file_uploader("Upload CSV File", type=["csv"])

    if uploaded_file is None:
        st.info("Please upload a CSV file to continue.")
        return

    df = load_and_preprocess_data(uploaded_file)

    indicator_options = ["All"]
    if "Indicator" in df.columns:
        indicator_options += sorted(df["Indicator"].unique())

    indicator_filter = st.sidebar.selectbox("Select Indicator", indicator_options)
    top_n = st.sidebar.slider("Top Countries", 5, 20, 10)

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Summary", "Charts", "Trends", "Export"]
    )

    with tab1:
        dataset_summary(df)

    with tab2:
        plot_pie_clean(df)
        plot_time_series(df, indicator_filter)
        plot_bar_top_countries(df, top_n)
        plot_correlation_heatmap(df)

    with tab3:
        analyze_trends(df, indicator_filter)
        plot_scatter_trends(df, indicator_filter)
        plot_indicator_slope_scatter(df)  # ✅ ADDITION

    with tab4:
        export_filtered_data(df, indicator_filter)

# -------------------------------
# RUN
# -------------------------------
if __name__ == "__main__":
    main()
