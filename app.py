import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ── Page Config ───────────────────────────────────────────
st.set_page_config(page_title="Retention Analytics", layout="wide")
st.title("🏦 Customer Engagement & Retention Analytics")
st.caption("Unified Mentor: European Central Bank | Analytical Dashboard")

# ── Load Data ─────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv(r"C:\Users\MOHINI\Downloads\bank_churn.csv")
    median_balance = df['Balance'].median()

    def classify_engagement(row):
        active = row['IsActiveMember'] == 1
        multi_product = row['NumOfProducts'] > 1
        high_balance = row['Balance'] > median_balance
        if active and multi_product:
            return 'Active Engaged'
        elif active and not multi_product:
            return 'Active Low-Product'
        elif not active and high_balance:
            return 'Inactive High-Balance'
        else:
            return 'Inactive Disengaged'

    df['EngagementProfile'] = df.apply(classify_engagement, axis=1)
    df['ProductDepth'] = df['NumOfProducts'].apply(lambda x: 'Single' if x == 1 else 'Multi')
    df['RSI'] = (
        df['IsActiveMember'] * 0.4 +
        (df['NumOfProducts'] / df['NumOfProducts'].max()) * 0.4 +
        (df['HasCrCard'] * 0.2)
    )
    return df

df = load_data()

# ── Sidebar Filters ───────────────────────────────────────
st.sidebar.header("Filters")
selected_profiles = st.sidebar.multiselect(
    "Engagement Profile",
    options=df['EngagementProfile'].unique(),
    default=df['EngagementProfile'].unique()
)
product_range = st.sidebar.slider("Number of Products", 1, int(df['NumOfProducts'].max()), (1, 4))
balance_range = st.sidebar.slider(
    "Balance Range",
    float(df['Balance'].min()),
    float(df['Balance'].max()),
    (float(df['Balance'].min()), float(df['Balance'].max()))
)
salary_threshold = st.sidebar.slider(
    "Min Estimated Salary",
    float(df['EstimatedSalary'].min()),
    float(df['EstimatedSalary'].max()),
    float(df['EstimatedSalary'].min())
)

# ── Apply Filters ─────────────────────────────────────────
filtered = df[
    (df['EngagementProfile'].isin(selected_profiles)) &
    (df['NumOfProducts'].between(*product_range)) &
    (df['Balance'].between(*balance_range)) &
    (df['EstimatedSalary'] >= salary_threshold)
]

# ── KPI Cards ─────────────────────────────────────────────
st.subheader("Key Performance Indicators")
k1, k2, k3, k4, k5 = st.columns(5)

active_churn = filtered[filtered['IsActiveMember'] == 1]['Exited'].mean()
inactive_churn = filtered[filtered['IsActiveMember'] == 0]['Exited'].mean()
err = round(inactive_churn / active_churn, 2) if active_churn else 0

high_bal = filtered['Balance'].quantile(0.75)
hbdr = filtered[(filtered['Balance'] >= high_bal) & (filtered['IsActiveMember'] == 0)].shape[0]
hbdr_pct = round(hbdr / max(filtered[filtered['Balance'] >= high_bal].shape[0], 1) * 100, 1)

multi_ret = filtered[(filtered['ProductDepth'] == 'Multi') & (filtered['Exited'] == 0)].shape[0]
single_ret = filtered[(filtered['ProductDepth'] == 'Single') & (filtered['Exited'] == 0)].shape[0]
pdi = round(multi_ret / max(single_ret, 1), 2)

card_churn = filtered[filtered['HasCrCard'] == 1]['Exited'].mean()
no_card_churn = filtered[filtered['HasCrCard'] == 0]['Exited'].mean()
ccs = round(no_card_churn / max(card_churn, 0.001), 2)

avg_rsi = round(filtered['RSI'].mean(), 3)

k1.metric("Engagement Retention Ratio", err)
k2.metric("Product Depth Index", pdi)
k3.metric("High-Balance Disengagement %", f"{hbdr_pct}%")
k4.metric("CC Stickiness Score", ccs)
k5.metric("Avg Relationship Strength", avg_rsi)

st.divider()

# ── Module 1: Engagement vs Churn ─────────────────────────
st.subheader("1. Engagement vs Churn Overview")
eng_churn = filtered.groupby('EngagementProfile')['Exited'].mean().reset_index()
eng_churn['ChurnRate'] = (eng_churn['Exited'] * 100).round(2)
fig1 = px.bar(eng_churn, x='EngagementProfile', y='ChurnRate',
              color='ChurnRate', color_continuous_scale='Reds',
              title='Churn Rate by Engagement Profile')
st.plotly_chart(fig1, use_container_width=True)

# ── Module 2: Product Utilization ─────────────────────────
st.subheader("2. Product Utilization Impact")
prod_churn = filtered.groupby('NumOfProducts')['Exited'].mean().reset_index()
prod_churn['ChurnRate'] = (prod_churn['Exited'] * 100).round(2)
fig2 = px.bar(prod_churn, x='NumOfProducts', y='ChurnRate',
              color='ChurnRate', color_continuous_scale='Blues',
              title='Churn Rate by Number of Products')
st.plotly_chart(fig2, use_container_width=True)

# ── Module 3: High-Value Disengaged Detector ──────────────
st.subheader("3. High-Value Disengaged Customers")
at_risk = filtered[
    (filtered['Balance'] >= filtered['Balance'].quantile(0.75)) &
    (filtered['IsActiveMember'] == 0)
][['CustomerId', 'Surname', 'Balance', 'NumOfProducts', 'EstimatedSalary', 'Exited', 'RSI']]
st.dataframe(at_risk.sort_values('Balance', ascending=False).reset_index(drop=True), use_container_width=True)

# ── Module 4: Retention Strength Scoring ──────────────────
st.subheader("4. Retention Strength Distribution")
fig4 = px.histogram(filtered, x='RSI', color='EngagementProfile',
                    nbins=20, title='Relationship Strength Index by Engagement Profile',
                    barmode='overlay', opacity=0.7)
st.plotly_chart(fig4, use_container_width=True)