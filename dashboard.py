import streamlit as st
import pandas as pd
import plotly.express as px
import os
from pathlib import Path

# Page config
st.set_page_config(
    page_title="Healthcare Marketplace Dashboard",
    page_icon="🏥",
    layout="wide"
)

# Load data function
@st.cache_data
def load_data():
    data_dir = Path("exported_csvs")
    data = {}
    for file in data_dir.glob("*.csv"):
        name = file.stem
        data[name] = pd.read_csv(file)
    return data

# Load all data
data = load_data()

# Sidebar filters
st.sidebar.title("Filters")
selected_plans = st.sidebar.multiselect(
    "Select Plans",
    options=data['plans']['name'].unique() if 'plans' in data else []
)

# Main dashboard
st.title("Healthcare Marketplace Dashboard")

# Summary cards
if 'plans' in data:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Plans", len(data['plans']))
    with col2:
        st.metric("Unique Issuers", data['issuers']['name'].nunique() if 'issuers' in data else 0)
    with col3:
        st.metric("Avg Premium", f"${data['plans']['premium'].mean():.2f}" if 'plans' in data else "N/A")

# Plans by Metal Level
if 'plans' in data:
    st.subheader("Plans by Metal Level")
    metal_counts = data['plans']['metal_level'].value_counts().reset_index()
    metal_counts.columns = ['Metal Level', 'Count']
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        fig = px.bar(
            metal_counts,
            x='Metal Level',
            y='Count',
            color='Metal Level',
            title="Number of Plans by Metal Level"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.dataframe(
            data['plans'][['name', 'metal_level', 'premium']].sort_values('premium'),
            hide_index=True,
            use_container_width=True
        )

# Benefits Coverage
if 'benefits' in data:
    st.subheader("Benefits Coverage")
    benefit_coverage = data['benefits'].groupby('name')['covered'].mean().reset_index()
    benefit_coverage.columns = ['Benefit', 'Coverage Rate']
    benefit_coverage['Coverage Rate'] = (benefit_coverage['Coverage Rate'] * 100).round(1)
    
    fig = px.bar(
        benefit_coverage,
        x='Coverage Rate',
        y='Benefit',
        orientation='h',
        title="Percentage of Plans Covering Each Benefit"
    )
    st.plotly_chart(fig, use_container_width=True)

# Premium Distribution
if 'plans' in data and 'metal_level' in data['plans']:
    st.subheader("Premium Distribution by Metal Level")
    fig = px.box(
        data['plans'],
        x='metal_level',
        y='premium',
        color='metal_level',
        title="Premium Distribution by Metal Level"
    )
    st.plotly_chart(fig, use_container_width=True)

# Raw Data Explorer
st.subheader("Data Explorer")
selected_table = st.selectbox(
    "Select Table to Explore",
    list(data.keys())
)

if selected_table in data:
    st.dataframe(data[selected_table], use_container_width=True)