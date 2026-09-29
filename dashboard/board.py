import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path


# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="E-Commerce Analytics",
    page_icon="📊",
    layout="wide"
)

st.title("E-Commerce Revenue & Customer Intelligence")
st.caption("Interactive analysis of sales, customers, and profitability")


# --------------------------------------------------
# DATA
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "ecommerce_sales_customer_analytics_150k.csv"


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)

    df["order_date"] = pd.to_datetime(
        df["order_date"],
        errors="coerce"
    )

    df["order_month"] = (
        df["order_date"]
        .dt.to_period("M")
        .dt.to_timestamp()
    )

    return df


df = load_data()

ORDERS_PATH = PROJECT_ROOT / "data" / "order_items.csv"


@st.cache_data
def load_orders():
    return pd.read_csv(ORDERS_PATH)


df_orders = load_orders()

# --------------------------------------------------
# SIDEBAR FILTERS
# --------------------------------------------------

st.sidebar.header("Filters")

# Date range
min_date = df["order_date"].min().date()
max_date = df["order_date"].max().date()

date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Region
regions = sorted(df["region"].dropna().unique())

selected_regions = st.sidebar.multiselect(
    "Region",
    options=regions,
    default=regions
)

# Customer segment
segments = sorted(df["customer_segment"].dropna().unique())

selected_segments = st.sidebar.multiselect(
    "Customer Segment",
    options=segments,
    default=segments
)

# Sales channel
channels = sorted(df["sales_channel"].dropna().unique())

selected_channels = st.sidebar.multiselect(
    "Sales Channel",
    options=channels,
    default=channels
)

# --------------------------------------------------
# APPLY FILTERS
# --------------------------------------------------

start_date, end_date = date_range

filtered_df = df[
    (df["order_date"].dt.date >= start_date) &
    (df["order_date"].dt.date <= end_date) &
    (df["region"].isin(selected_regions)) &
    (df["customer_segment"].isin(selected_segments)) &
    (df["sales_channel"].isin(selected_channels))
].copy()


tab_exec, tab_h1, tab_h2, tab_h3, tab_h4 = st.tabs([
    "Executive Overview",
    "H1: Acquisition Cost",
    "H2: Customer Segments",
    "H3: Customer Age",
    "H4: Discounts"
])

with tab_exec:

    # --------------------------------------------------
    # KPI CALCULATIONS
    # --------------------------------------------------

    total_revenue = filtered_df["net_sales"].sum()
    total_profit = filtered_df["profit"].sum()

    total_orders = filtered_df["order_id"].nunique()
    total_customers = filtered_df["customer_id"].nunique()

    average_order_value = (
        total_revenue / total_orders
        if total_orders > 0 else 0
    )

    profit_margin = (
        (total_profit / total_revenue) * 100
        if total_revenue > 0 else 0
    )

    # --------------------------------------------------
    # KPI CARDS
    # --------------------------------------------------

    st.subheader("Executive Overview")

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    col1.metric(
        "Net Revenue",
        f"${total_revenue:,.0f}"
    )

    col2.metric(
        "Profit",
        f"${total_profit:,.0f}"
    )

    col3.metric(
        "Profit Margin",
        f"{profit_margin:.1f}%"
    )

    col4.metric(
        "Orders",
        f"{total_orders:,}"
    )

    col5.metric(
        "Customers",
        f"{total_customers:,}"
    )

    col6.metric(
        "Average Order Value",
        f"${average_order_value:,.0f}"
    )

    # --------------------------------------------------
    # MONTHLY PERFORMANCE
    # --------------------------------------------------

    monthly_kpis = (
        filtered_df
        .groupby("order_month")
        .agg(
            revenue=("net_sales", "sum"),
            profit=("profit", "sum"),
            orders=("order_id", "nunique"),
            customers=("customer_id", "nunique")
        )
        .reset_index()
    )

    monthly_kpis["aov"] = (
        monthly_kpis["revenue"]
        / monthly_kpis["orders"]
    )

    monthly_kpis["revenue_growth"] = (
        monthly_kpis["revenue"]
        .pct_change() * 100
    )


    st.subheader("Revenue Performance")

    fig = px.line(
        monthly_kpis,
        x="order_month",
        y="revenue",
        markers=True,
        labels={
            "order_month": "Month",
            "revenue": "Net Revenue"
        }
    )

    fig.update_layout(
        xaxis_title=None,
        yaxis_title="Net Revenue ($)",
        hovermode="x unified"
    )

    fig.update_yaxes(
        tickprefix="$",
        tickformat=",.0f"
    )

    st.plotly_chart(
        fig,
        width="stretch",
        key = "monthly_revenue_chart"
    )

    # --------------------------------------------------
    # REVENUE BY SALES CHANNEL
    # --------------------------------------------------

    channel_performance = (
        filtered_df
        .groupby("sales_channel")
        .agg(
            revenue=("net_sales", "sum"),
            profit=("profit", "sum"),
            orders=("order_id", "nunique")
        )
        .reset_index()
        .sort_values("revenue", ascending=False)
    )

    fig_channel = px.bar(
        channel_performance,
        x="sales_channel",
        y="revenue",
        title="Revenue by Sales Channel",
        labels={
            "sales_channel": "Sales Channel",
            "revenue": "Net Revenue"
        }
    )

    fig_channel.update_layout(
        xaxis_title=None,
        yaxis_title="Net Revenue ($)"
    )

    fig_channel.update_yaxes(
        tickprefix="$",
        tickformat=",.0f"
    )


    # --------------------------------------------------
    # REVENUE VS PROFIT
    # --------------------------------------------------

    fig_performance = go.Figure()

    fig_performance.add_trace(
        go.Scatter(
            x=monthly_kpis["order_month"],
            y=monthly_kpis["revenue"],
            mode="lines+markers",
            name="Revenue"
        )
    )

    fig_performance.add_trace(
        go.Scatter(
            x=monthly_kpis["order_month"],
            y=monthly_kpis["profit"],
            mode="lines+markers",
            name="Profit"
        )
    )

    fig_performance.update_layout(
        title="Revenue and Profit Over Time",
        xaxis_title=None,
        yaxis_title="Amount ($)",
        hovermode="x unified"
    )

    fig_performance.update_yaxes(
        tickprefix="$",
        tickformat=",.0f"
    )

    st.plotly_chart(
        fig_performance,
        width="stretch",
        key="revenue_profit_chart"
    )

    # --------------------------------------------------
    # REVENUE BY REGION
    # --------------------------------------------------

    region_performance = (
        filtered_df
        .groupby("region")
        .agg(
            revenue=("net_sales", "sum"),
            profit=("profit", "sum"),
            orders=("order_id", "nunique")
        )
        .reset_index()
        .sort_values("revenue", ascending=False)
    )

    fig_region = px.bar(
        region_performance,
        x="region",
        y="revenue",
        title="Revenue by Region",
        labels={
            "region": "Region",
            "revenue": "Net Revenue"
        }
    )

    fig_region.update_layout(
        xaxis_title=None,
        yaxis_title="Net Revenue ($)"
    )

    fig_region.update_yaxes(
        tickprefix="$",
        tickformat=",.0f"
    )

    left_col, right_col = st.columns(2)

    with left_col:
        st.plotly_chart(
            fig_channel,
            width="stretch",
            key="sales_channel_chart"
        )

    with right_col:
        st.plotly_chart(
            fig_region,
            width="stretch",
            key="region_chart"
        )


with tab_h1:

    # --------------------------------------------------
    # H1: CUSTOMER ACQUISITION COST VS PROFIT
    # --------------------------------------------------

    st.subheader("Does Acquisition Cost Predict Customer Profit?")

    st.write(
        """
        **H₀**: There is no statistically significant relationship between customer acquisition cost and customer value.

        **H₁**: There is a statistically significant relationship between customer acquisition cost and customer value.
        """
    )

    CUSTOMER_PATH = PROJECT_ROOT / "data" / "customer_master.csv"


    @st.cache_data
    def load_customers():
        return pd.read_csv(CUSTOMER_PATH)


    df_customers = load_customers()

    customer_value = (
        filtered_df
        .groupby("customer_id")
        .agg(
            total_profit=("profit", "sum"),
            total_revenue=("net_sales", "sum"),
            total_orders=("order_id", "nunique")
        )
        .reset_index()
    )

    customer_analysis = customer_value.merge(
        df_customers[
            ["customer_id", "customer_acquisition_cost"]
        ],
        on="customer_id",
        how="inner"
    )

    from scipy.stats import spearmanr, pearsonr

    analysis_data = customer_analysis[
        ["customer_acquisition_cost", "total_profit"]
    ].dropna()

    spearman_rho, spearman_p = spearmanr(
        analysis_data["customer_acquisition_cost"],
        analysis_data["total_profit"]
    )

    pearson_r, pearson_p = pearsonr(
        analysis_data["customer_acquisition_cost"],
        analysis_data["total_profit"]
    )

    fig_h1 = px.scatter(
        analysis_data,
        x="customer_acquisition_cost",
        y="total_profit",
        opacity=0.25,
        trendline="ols",
        title="Acquisition Cost vs Customer Profit",
        labels={
            "customer_acquisition_cost": "Customer Acquisition Cost ($)",
            "total_profit": "Total Customer Profit ($)"
        }
    )

    st.plotly_chart(
        fig_h1,
        width="stretch",
        key="h1_cac_profit"
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Spearman Correlation",
        f"{spearman_rho:.4f}"
    )

    col2.metric(
        "P-value",
        f"{spearman_p:.4f}"
    )

    col3.metric(
        "Customers Analysed",
        f"{len(analysis_data):,}"
    )


    alpha = 0.05

    if spearman_p < alpha:
        st.success(
            f"""
            **Result**

            The Spearman rank correlation found a statistically significant association 
            between customer acquisition cost and total customer profit 
            (ρ = {spearman_rho:.4f}, p = {spearman_p:.4g}, n = {len(analysis_data):,}).

            At a significance level of α = 0.05, the null hypothesis is rejected.

            **Business Interpretation**

            Within the selected data, customer acquisition cost is statistically associated 
            with customer profitability. However, the magnitude of the correlation should 
            also be considered when determining whether this relationship is practically 
            meaningful for the business.

            A statistically significant result does not necessarily mean that acquisition 
            cost is a strong predictor of customer profitability.
            """
        )

    else:
        st.info(
            f"""
            **Result**

            The Spearman rank correlation found virtually no association between customer 
            acquisition cost and total customer profit 
            (ρ = {spearman_rho:.4f}, p = {spearman_p:.4g}, n = {len(analysis_data):,}).

            At a significance level of α = 0.05, the null hypothesis is not rejected.

            **Business Interpretation**

            Within the selected data, customers who cost more to acquire do not tend to 
            generate higher or lower total profit. Higher customer acquisition spending 
            therefore does not appear to be associated with greater customer profitability.

            This suggests that acquisition cost alone would not be useful for identifying 
            higher-value customers. Other customer characteristics or acquisition factors 
            may provide more useful information for targeting profitable customers.
            """
        )


with tab_h2:

    st.subheader("Do Customers From Different Customer Segments Generate Different Levels Of Revenue?")

    st.markdown(
        """
        **H₀:** Mean customer revenue is equal across all customer segments.

        **H₁:** At least one customer segment has a different mean
        customer revenue.
        """
    )

    # ----------------------------------------------
    # CUSTOMER-LEVEL DATA
    # ----------------------------------------------

    customer_segment_analysis = (
        filtered_df
        .groupby("customer_id")
        .agg(
            total_revenue=("net_sales", "sum"),
            total_profit=("profit", "sum"),
            total_orders=("order_id", "nunique")
        )
        .reset_index()
    )

    customer_segment_analysis = customer_segment_analysis.merge(
        df_customers[
            ["customer_id", "customer_segment"]
        ],
        on="customer_id",
        how="inner"
    )

    segment_summary = (
        customer_segment_analysis
        .groupby("customer_segment")
        .agg(
            customers=("customer_id", "count"),
            mean_revenue=("total_revenue", "mean"),
            median_revenue=("total_revenue", "median")
        )
        .reset_index()
    )

    fig_h2 = px.box(
        customer_segment_analysis,
        x="customer_segment",
        y="total_revenue",
        points=False,
        title="Customer Revenue by Customer Segment",
        labels={
            "customer_segment": "Customer Segment",
            "total_revenue": "Total Customer Revenue ($)"
        }
    )

    fig_h2.update_yaxes(
        tickprefix="$",
        tickformat=",.0f"
    )

    st.plotly_chart(
        fig_h2,
        width="stretch",
        key="h2_segment_revenue"
    )

    from statsmodels.stats.oneway import anova_oneway

    segment_groups = [
        group["total_revenue"].dropna().values
        for _, group in customer_segment_analysis.groupby(
            "customer_segment"
        )
    ]

    welch_result = anova_oneway(
        segment_groups,
        use_var="unequal"
    )

    welch_stat = welch_result.statistic
    welch_p = welch_result.pvalue

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Welch ANOVA Statistic",
        f"{welch_stat:.4f}"
    )

    col2.metric(
        "P-value",
        f"{welch_p:.4g}"
    )

    col3.metric(
        "Customers Analysed",
        f"{len(customer_segment_analysis):,}"
    )

    alpha = 0.05

    if welch_p < alpha:
        st.success(
            f"""
            **Result**

            Welch's one-way ANOVA found a statistically significant
            difference in mean customer revenue across customer segments
            (F = {welch_stat:.4f}, p = {welch_p:.4g},
            n = {len(customer_segment_analysis):,}).

            At a significance level of α = 0.05, the null hypothesis
            is rejected.

            **Business Interpretation**

            Within the selected data, customer segment is associated
            with differences in average customer revenue.

            Further pairwise analysis would be required to determine
            which specific customer segments differ from one another.
            """
        )

    else:
        st.info(
            f"""
            **Result**

            Welch's one-way ANOVA found no statistically significant
            difference in mean customer revenue across customer segments
            (F = {welch_stat:.4f}, p = {welch_p:.4g},
            n = {len(customer_segment_analysis):,}).

            At a significance level of α = 0.05, the null hypothesis
            is not rejected.

            **Business Interpretation**

            Within the selected data, customers across the different
            segments generate similar levels of revenue on average.

            Customer segment alone therefore does not appear to be a
            useful way of distinguishing higher-revenue customers.
            """
        )



with tab_h3:

    st.header("Customer Age & Purchasing Behaviour")

    st.write(
        """
        **Business Question:**  
        Does customer age relate to purchasing behaviour?
        
        Purchasing behaviour is examined using total revenue,
        order frequency, and average order value.
        """
    )

    st.markdown(
        """
        **H₀:** Customer age is not associated with purchasing behaviour.

        **H₁:** Customer age is associated with purchasing behaviour.
        """
    )

    customer_age_analysis = (
        filtered_df
        .groupby("customer_id")
        .agg(
            total_revenue=("net_sales", "sum"),
            total_orders=("order_id", "nunique")
        )
        .reset_index()
    )

    customer_age_analysis["average_order_value"] = (
        customer_age_analysis["total_revenue"]
        / customer_age_analysis["total_orders"]
    )

    customer_age_analysis = customer_age_analysis.merge(
        df_customers[
            ["customer_id", "customer_age"]
        ],
        on="customer_id",
        how="inner"
    )

    customer_age_analysis = customer_age_analysis.dropna(
        subset=["customer_age"]
    )

    outcomes = {
        "Total Revenue": "total_revenue",
        "Order Frequency": "total_orders",
        "Average Order Value": "average_order_value"
    }

    correlation_results = {}

    for name, column in outcomes.items():

        analysis_data = customer_age_analysis[
            ["customer_age", column]
        ].dropna()

        rho, p = spearmanr(
            analysis_data["customer_age"],
            analysis_data[column]
        )

        correlation_results[name] = {
            "rho": rho,
            "p": p
        }

    col1, col2, col3 = st.columns(3)

    revenue_result = correlation_results["Total Revenue"]
    orders_result = correlation_results["Order Frequency"]
    aov_result = correlation_results["Average Order Value"]

    col1.metric(
        "Age ↔ Revenue",
        f"ρ = {revenue_result['rho']:.4f}",
        help=f"p = {revenue_result['p']:.4g}"
    )

    col2.metric(
        "Age ↔ Order Frequency",
        f"ρ = {orders_result['rho']:.4f}",
        help=f"p = {orders_result['p']:.4g}"
    )

    col3.metric(
        "Age ↔ AOV",
        f"ρ = {aov_result['rho']:.4f}",
        help=f"p = {aov_result['p']:.4g}"
    )

    results_df = pd.DataFrame([
        {
            "Measure": name,
            "Spearman ρ": result["rho"],
            "P-value": result["p"]
        }
        for name, result in correlation_results.items()
    ])

    st.dataframe(
        results_df.style.format({
            "Spearman ρ": "{:.4f}",
            "P-value": "{:.4f}"
        }),
        hide_index=True,
        width="stretch"
    )

    age_bins = [0, 24, 34, 44, 54, 64, float("inf")]

    age_labels = [
        "Under 25",
        "25–34",
        "35–44",
        "45–54",
        "55–64",
        "65+"
    ]

    customer_age_analysis["age_group"] = pd.cut(
        customer_age_analysis["customer_age"],
        bins=age_bins,
        labels=age_labels
    )

    age_summary = (
        customer_age_analysis
        .groupby("age_group", observed=True)
        .agg(
            mean_revenue=("total_revenue", "mean"),
            mean_orders=("total_orders", "mean"),
            mean_aov=("average_order_value", "mean")
        )
        .reset_index()
    )

    metric_choice = st.selectbox(
        "Purchasing Measure",
        [
            "Average Revenue",
            "Average Orders",
            "Average Order Value"
        ]
    )

    metric_map = {
        "Average Revenue": "mean_revenue",
        "Average Orders": "mean_orders",
        "Average Order Value": "mean_aov"
    }

    selected_metric = metric_map[metric_choice]

    fig_h3 = px.bar(
        age_summary,
        x="age_group",
        y=selected_metric,
        title=f"{metric_choice} by Age Group",
        labels={
            "age_group": "Age Group",
            selected_metric: metric_choice
        }
    )

    if selected_metric != "mean_orders":
        fig_h3.update_yaxes(
            tickprefix="$",
            tickformat=",.0f"
        )

    st.plotly_chart(
        fig_h3,
        width="stretch",
        key="h3_age_analysis"
    )

    alpha = 0.05

    significant_results = {
        name: result
        for name, result in correlation_results.items()
        if result["p"] < alpha
    }

    if significant_results:
        significant_names = ", ".join(significant_results.keys())

        st.success(
            f"""
            **Result**

            At least one purchasing behaviour measure showed a statistically
            significant association with customer age at α = 0.05.

            Significant measure(s): **{significant_names}**

            **Business Interpretation**

            Within the selected data, customer age is associated with at least
            one aspect of purchasing behaviour. However, the magnitude of the
            Spearman correlations should also be considered before concluding
            that age is practically useful for customer targeting.

            A statistically significant correlation does not necessarily imply
            that age is a strong predictor of purchasing behaviour.
            """
        )

    else:
        st.info(
            f"""
            **Result**

            Spearman rank correlations found no statistically significant
            association between customer age and any of the three purchasing
            behaviour measures examined:

            - **Total Revenue:** ρ = {revenue_result['rho']:.4f},
            p = {revenue_result['p']:.4g}
            - **Order Frequency:** ρ = {orders_result['rho']:.4f},
            p = {orders_result['p']:.4g}
            - **Average Order Value:** ρ = {aov_result['rho']:.4f},
            p = {aov_result['p']:.4g}

            At a significance level of α = 0.05, the null hypothesis is not
            rejected for any of the three measures.

            **Business Interpretation**

            Within the selected data, customer age does not appear to be
            associated with how much customers spend, how frequently they
            purchase, or how much they spend per order.

            This suggests that age alone would not be useful for identifying
            higher-value or more frequent customers. Other customer
            characteristics may provide more useful information for
            understanding purchasing behaviour.
            """
        )


with tab_h4:

    st.header("Discount Effectiveness")

    st.write(
        """
        **Business Question:**  
        How are product discounts associated with purchasing quantity
        and profitability?
        """
    )

    st.markdown(
        """
        **H₀:** Discount percentage is not associated with quantity
        purchased, net sales, or profit.

        **H₁:** Discount percentage is associated with at least one of
        these sales outcomes.
        """
    )

    # --------------------------------------------------
    # FILTER ORDER-ITEM DATA
    # --------------------------------------------------

    # Use order IDs remaining after the global filters
    selected_order_ids = filtered_df["order_id"].unique()

    discount_analysis = df_orders[
        df_orders["order_id"].isin(selected_order_ids)
    ].copy()

    # Convert decimal discount to percentage
    discount_analysis["discount_pct"] = (
        discount_analysis["discount_percentage"] * 100
    )

    discount_analysis = discount_analysis.dropna(
        subset=[
            "discount_pct",
            "quantity",
            "net_sales",
            "profit"
        ]
    )

    # --------------------------------------------------
    # SPEARMAN CORRELATIONS
    # --------------------------------------------------

    discount_outcomes = {
        "Quantity Sold": "quantity",
        "Net Sales": "net_sales",
        "Profit": "profit"
    }

    discount_results = {}

    for name, column in discount_outcomes.items():

        rho, p = spearmanr(
            discount_analysis["discount_pct"],
            discount_analysis[column]
        )

        discount_results[name] = {
            "rho": rho,
            "p": p
        }

    results_df = pd.DataFrame([
        {
            "Measure": name,
            "Spearman ρ": result["rho"],
            "P-value": result["p"]
        }
        for name, result in discount_results.items()
    ])

    st.subheader("Statistical Results")

    st.dataframe(
        results_df.style.format({
            "Spearman ρ": "{:.4f}",
            "P-value": "{:.4g}"
        }),
        hide_index=True,
        width="stretch"
    )

    # --------------------------------------------------
    # DISCOUNT GROUPS
    # --------------------------------------------------

    discount_bins = [
        -0.01,
        0,
        5,
        10,
        15,
        20,
        30,
        40,
        50,
        float("inf")
    ]

    discount_labels = [
        "No Discount",
        "0–5%",
        "5–10%",
        "10–15%",
        "15–20%",
        "20–30%",
        "30–40%",
        "40–50%",
        "50%+"
    ]

    discount_analysis["discount_group"] = pd.cut(
        discount_analysis["discount_pct"],
        bins=discount_bins,
        labels=discount_labels
    )

    discount_summary = (
        discount_analysis
        .groupby("discount_group", observed=True)
        .agg(
            transactions=("product_id", "count"),
            mean_quantity=("quantity", "mean"),
            mean_net_sales=("net_sales", "mean"),
            mean_profit=("profit", "mean")
        )
        .reset_index()
    )

    st.subheader("Performance by Discount Level")

    metric_choice = st.selectbox(
        "Select outcome",
        [
            "Average Quantity",
            "Average Net Sales",
            "Average Profit"
        ],
        key="h4_metric_choice"
    )

    metric_map = {
        "Average Quantity": "mean_quantity",
        "Average Net Sales": "mean_net_sales",
        "Average Profit": "mean_profit"
    }

    selected_metric = metric_map[metric_choice]

    fig_h4 = px.bar(
        discount_summary,
        x="discount_group",
        y=selected_metric,
        title=f"{metric_choice} by Discount Level",
        labels={
            "discount_group": "Discount Level",
            selected_metric: metric_choice
        }
    )

    if selected_metric != "mean_quantity":
        fig_h4.update_yaxes(
            tickprefix="$",
            tickformat=",.0f"
        )

    st.plotly_chart(
        fig_h4,
        width="stretch",
        key="h4_discount_performance"
    )

    quantity_result = discount_results["Quantity Sold"]
    sales_result = discount_results["Net Sales"]
    profit_result = discount_results["Profit"]

    alpha = 0.05

    st.info(
        f"""
        **Result**

        Spearman rank correlation found:

        - **Quantity Sold:** ρ = {quantity_result['rho']:.4f},
          p = {quantity_result['p']:.4g}
        - **Net Sales:** ρ = {sales_result['rho']:.4f},
          p = {sales_result['p']:.4g}
        - **Profit:** ρ = {profit_result['rho']:.4f},
          p = {profit_result['p']:.4g}

        **Business Interpretation**

        {
            "Higher discount levels are associated with larger purchase quantities."
            if quantity_result["rho"] > 0 and quantity_result["p"] < alpha
            else
            "No statistically significant positive association between discounts and purchase quantity was detected."
        }

        {
            "The relationship between discount level and net sales is statistically significant, but its magnitude is very small."
            if sales_result["p"] < alpha and abs(sales_result["rho"]) < 0.05
            else
            "The relationship between discount level and net sales should be interpreted based on both its statistical significance and correlation magnitude."
        }

        {
            "Higher discount levels are associated with lower transaction profitability."
            if profit_result["rho"] < 0 and profit_result["p"] < alpha
            else
            "No statistically significant negative association between discounts and profitability was detected."
        }

        The relationship between discount and quantity should **not be
        interpreted causally**. Larger purchases may receive larger
        discounts rather than larger discounts causing customers to
        purchase more.

        Overall, the selected data should be evaluated for a potential
        trade-off between transaction volume and profitability.
        """
    )

    high_discount = discount_summary[
        discount_summary["discount_group"] == "50%+"
    ]

    if not high_discount.empty:

        high_discount_profit = high_discount["mean_profit"].iloc[0]

        if high_discount_profit < 0:
            st.warning(
                f"""
                **High Discount Alert:** Transactions receiving discounts
                above 50% generated an average profit of
                **${high_discount_profit:,.2f}** within the selected data.
                """
            )