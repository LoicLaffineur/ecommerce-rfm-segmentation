import pandas as pd 
import plotly.express as px
import streamlit as st

@st.cache_data(show_spinner="Loading data…")
def load_data(file:str = "data/data_cleaned.csv") -> pd.DataFrame: 
    df = pd.read_csv(file)

    # Drop unused columns and non-country rows
    df.drop(columns=['QuantityCanceled'], inplace=True, errors="ignore")
    delete = ["European Community", "Unspecified", "Channel Islands"]
    df.drop(index=df[df["Country"].isin(delete)].index, inplace=True)

    # Cast types and normalize country labels
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    df['CustomerID'] = df['CustomerID'].astype('object')
    df['InvoiceNo'] = df['InvoiceNo'].astype('object')
    df["Country"] = df["Country"].replace({"EIRE": "Ireland", "RSA": "South Africa"})   

    # Derived columns
    df['Revenue'] = df['Quantity'] * df['UnitPrice']
    df['Month'] = df['InvoiceDate'].dt.to_period("M")  # YYYY-MM period

    return df

@st.cache_data(show_spinner="Computing customer KPIs…")
def compute_client_kpi(df) : 
    orders = df.groupby(["CustomerID","InvoiceNo"]).agg(
        order_date = ("InvoiceDate","min"),
        order_revenue = ("Revenue","sum"), 
        )
    orders = orders.reset_index()

    kpi_client = orders.groupby(["CustomerID"]).agg(
        n_orders = ("InvoiceNo","nunique"),
        total_revenue = ("order_revenue","sum"),
        first_order = ("order_date","min"),
        last_order = ("order_date","max"),
        )

    kpi_client["avg_order_value"] = kpi_client["total_revenue"] / kpi_client["n_orders"]
    
    # Interpurchase time : (median days between orders)
    keep =["CustomerID","order_date"] 
    sorted_orders=orders[keep].sort_values(by=keep)

    delta_days = sorted_orders.groupby("CustomerID")['order_date'].diff().dt.days
    interpurchase_median = delta_days.groupby(sorted_orders["CustomerID"]).median()
    interpurchase_median.name = "interpurchase_median"
    kpi_client = kpi_client.join(interpurchase_median, on="CustomerID")

    df_clust = pd.read_csv("data/data_clustered.csv")
    df_clust['CustomerID'] = df_clust['CustomerID'].astype('object')
    df_clust.drop(
        columns=["Monetary_log","Recency_log","Frequency_log"], 
        inplace=True, 
        errors="ignore"
        )

    kpi_final = pd.merge(df_clust, kpi_client, on="CustomerID")
    rev_q90 = kpi_final["total_revenue"].quantile(0.9)
    kpi_final["VIP"] = (kpi_final["Cluster"] == 4) | (
        (kpi_final["total_revenue"] > rev_q90) & (kpi_final["Recency"] < 30)
    )
    # Behavioural at-risk only when median inter-purchase is defined
    late_vs_cycle = kpi_final["interpurchase_median"].notna() & (
        kpi_final["Recency"] > 1.5 * kpi_final["interpurchase_median"]
    )
    kpi_final["At-risk"] = (kpi_final["Cluster"] == 3) | late_vs_cycle
    
    return kpi_final

@st.cache_data(show_spinner="Computing country KPIs…")
def compute_country_kpi(df, month=False) : 

    if month :  # Group by country and month
        kpi_map = df.groupby(["Country", "Month"]).agg(
            CA = ('Revenue','sum'),
            n_order = ("InvoiceNo","nunique"),
            n_customer = ("CustomerID","nunique")
            )   
        kpi_map["mean_basket"] = kpi_map["CA"] / kpi_map["n_order"]
        kpi_map.reset_index(inplace=True)
        return kpi_map

    kpi_map = df.groupby(["Country"]).agg(
        CA = ('Revenue','sum'),
        n_order = ("InvoiceNo","nunique"),
        n_customer = ("CustomerID","nunique")
        )   
    kpi_map["mean_basket"] = kpi_map["CA"] / kpi_map["n_order"]
    kpi_map.reset_index(inplace=True)
    return kpi_map


# Internal column names (used in groupby / Plotly). UI labels are English.
COUNTRY_METRIC_KEYS = ("CA", "n_order", "n_customer", "mean_basket")
COUNTRY_METRIC_LABELS = {
    "CA": "Revenue",
    "n_order": "Orders",
    "n_customer": "Customers",
    "mean_basket": "Avg. order value",
}


def country_kpi_display_names(df: pd.DataFrame) -> pd.DataFrame:
    # Copy with KPI columns renamed for display only (Plotly still uses internal names).
    return df.rename(columns=COUNTRY_METRIC_LABELS)


METRIC_MAP = {
    "CA": {
        "title": "Revenue by country",
        "hover_data": {
            "CA": ":.0f",
            "n_order": True,
            "n_customer": True,
            "mean_basket": ":.2f",
        },
    },
    "n_customer": {
        "title": "Customers by country",
        "hover_data": {
            "CA": ":.0f",
            "n_order": True,
            "n_customer": True,
            "mean_basket": ":.2f",
        },
    },
    "n_order": {
        "title": "Orders by country",
        "hover_data": {
            "CA": ":.0f",
            "n_order": True,
            "n_customer": True,
            "mean_basket": ":.2f",
        },
    },
    "mean_basket": {
        "title": "Average basket by country",
        "hover_data": {
            "CA": ":.0f",
            "n_order": True,
            "n_customer": True,
            "mean_basket": ":.2f",
        },
    },
}

def render_overview(df_country:pd.DataFrame, metric:str) -> None:
    mapping = METRIC_MAP[metric]
    st.subheader(mapping["title"])

    fig = px.choropleth(
        df_country,
        locations="Country",
        locationmode="country names",
        color=metric,
        hover_name="Country",
        hover_data=mapping["hover_data"],
        color_continuous_scale="Turbo",
    )
    fig.update_geos(showcoastlines=True, showcountries=True, projection_type="natural earth")
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        coloraxis_colorbar=dict(title=COUNTRY_METRIC_LABELS[metric]),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top 10")
    top10 = df_country.sort_values(metric, ascending=False).head(10)
    st.dataframe(country_kpi_display_names(top10), use_container_width=True)