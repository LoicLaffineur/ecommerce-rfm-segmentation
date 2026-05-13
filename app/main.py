# python3 -m streamlit run app/main.py

import streamlit as st
import pandas as pd
import altair as alt
from app.functions import (
    COUNTRY_METRIC_KEYS,
    COUNTRY_METRIC_LABELS,
    country_kpi_display_names,
    load_data,
    compute_client_kpi,
    compute_country_kpi,
    render_overview,
)

st.set_page_config(layout="wide", page_title="Online Retail - Dashboard")

st.title("Online Retail - Dashboard")

df = load_data()
df_client = compute_client_kpi(df)

tab_country, tab_client, tab_segmentation = st.tabs(
    ["Country view", "Customer view", "Segmentation"]
)

with tab_country : 
    st.subheader("KPIs by country")
    df_country = compute_country_kpi(df)
    metric = st.selectbox(
        "Which metric should the map show?",
        COUNTRY_METRIC_KEYS,
        format_func=lambda k: COUNTRY_METRIC_LABELS[k],
    )
    render_overview(df_country, metric)
    st.divider()
    st.subheader("Full table")
    st.dataframe(
        country_kpi_display_names(df_country.sort_values(by=metric, ascending=False))
    )

with tab_client :
    st.subheader("KPIs by customer")
    customer_ids_all = (
        df_client["CustomerID"]
        .dropna()
        .astype(str)
        .drop_duplicates()
        .tolist()
    )
    customer_ids_all = sorted(
        customer_ids_all,
        key=lambda x: (not x.isdigit(), int(x) if x.isdigit() else x),
    )

    query = st.text_input(
        "Search CustomerID (e.g. 17850)",
        value=st.session_state.get("customer_query", ""),
        placeholder="Type part of the ID…",
    ).strip()
    st.session_state["customer_query"] = query

    if query:
        q = query.lower()
        customer_ids = [cid for cid in customer_ids_all if q in cid.lower()]
        if not customer_ids:
            st.info("No customer matches the filter. Showing the full list.")
            customer_ids = customer_ids_all
    else:
        customer_ids = customer_ids_all

    previous = str(st.session_state.get("selected_customer_id", "")) if "selected_customer_id" in st.session_state else ""
    default_index = customer_ids.index(previous) if previous in customer_ids else 0

    selected_id = st.selectbox(
        "Select a CustomerID",
        customer_ids,
        index=default_index,
    )
    st.session_state["selected_customer_id"] = str(selected_id)
    row_df = df_client[df_client["CustomerID"].astype(str) == str(selected_id)]
    if row_df.empty:
        st.warning("Customer not found.")
        st.stop()
    row = row_df.iloc[0]

    is_vip = bool(row["VIP"]) if pd.notna(row.get("VIP")) else False
    is_atrisk = bool(row["At-risk"]) if pd.notna(row.get("At-risk")) else False

    stat_col, badge_col = st.columns([1, 2])
    with stat_col:
        if is_vip and is_atrisk:
            st.metric("Status", "VIP · At-risk")
            st.caption("VIP: Cluster 4 or Top 10% Revenue + Recency < 30 days.")
            st.caption(
                "At-risk: Cluster 3 or Recency > 1.5 × Median days between orders (when known)."
            )
        elif is_vip:
            st.metric("Status", "VIP")
            st.caption("VIP: Cluster 4 or Top 10% Revenue + Recency < 30 days.")
        elif is_atrisk:
            st.metric("Status", "At-risk")
            st.caption(
                "At-risk: Cluster 3 or Recency > 1.5 × Median days between orders (when known)."
            )
        else:
            st.metric("Status", "Standard")

    cols = st.columns(6)
    cols[0].metric("Cluster", int(row.get("Cluster", 0)))
    cols[1].metric("Recency", int(row.get("Recency", 0)))
    cols[2].metric("Number of orders", int(row.get("n_orders", 0)))
    cols[3].metric("Total spend", f"{float(row.get('total_revenue', 0)):.2f}")
    cols[4].metric("Average order value", f"{float(row.get('avg_order_value', 0)):.2f}")
    inter = row.get("interpurchase_median", None)
    cols[5].metric(
        "Interpurchase (median, days)",
        "NaN" if pd.isna(inter) else int(inter),
    )

    st.divider()
    st.subheader("Last order")
    d = df[df["CustomerID"].astype(str) == str(selected_id)]
    d_sorted = d.sort_values(by="InvoiceDate", ascending=False)
    last_order = d[d["InvoiceNo"] == d_sorted.iloc[0]["InvoiceNo"]]
    keep = ["CustomerID","Country","InvoiceNo","InvoiceDate","StockCode","Description","Quantity","UnitPrice","Revenue"]
    st.dataframe(last_order[keep])

with tab_segmentation : 
    kpi_clust = df_client.groupby(['Cluster']).agg(
        n_customer = ("CustomerID","nunique"),
        revenue = ("total_revenue","sum")
    )
    kpi_clust.reset_index(inplace=True)
    st.subheader("Bar chart: customers per cluster")
    st.bar_chart(kpi_clust, x="Cluster", y="n_customer")
    st.divider()
    st.subheader("Bar chart: revenue per cluster")
    st.bar_chart(kpi_clust, x="Cluster", y="revenue")
    st.divider()
    st.subheader("Cluster visualization")
    # Five clusters -> five distinct colors (ColorBrewer Set1 palette)
    palette5 = ["#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00"]
    clusters_sorted = sorted(df_client["Cluster"].dropna().unique().tolist())
    domain = [str(c) for c in clusters_sorted]
    range_ = palette5[: len(domain)]

    chart = (
        alt.Chart(df_client.assign(Cluster=df_client["Cluster"].astype(str)))
        .mark_circle(size=60, opacity=0.85)
        .encode(
            x=alt.X("PCA1:Q", title="PCA1"),
            y=alt.Y("PCA2:Q", title="PCA2"),
            color=alt.Color(
                "Cluster:N",
                scale=alt.Scale(domain=domain, range=range_),
                legend=alt.Legend(title="Cluster"),
            ),
            tooltip=["CustomerID:N", "Cluster:N", "PCA1:Q", "PCA2:Q"],
        )
        .interactive()
    )

    st.altair_chart(chart, use_container_width=True)