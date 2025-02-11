import pandas as pd
import plotly.express as px
import streamlit as st

# Streamlit title
st.title("📊 Stock Analysis Dashboard")

# Load and optimize data
@st.cache_data
def preprocess_data():
    # Load stock data
    stock_data = pd.read_excel('stock kos.xlsx', usecols=['Date', 'Product ID', 'Product Name',
                                                          'Start Available Stock', 'Inbound from PO', 'Inbound from SO Act Qty'],
                               dtype={'Product ID': 'category', 'Product Name': 'string'})
    
    # Load Pareto classification
    pareto_data = pd.read_csv('dash jan.csv', usecols=['Product ID', 'New Pareto A-D (Monthly)'],
                                 dtype={'Product ID': 'category'})
    
    # Merge datasets
    data = stock_data.merge(pareto_data, on='Product ID', how='left')
    
    for col in ['Start Available Stock', 'Inbound from PO', 'Inbound from SO Act Qty']:
        data[col] = pd.to_numeric(data[col], downcast='float')
    
    data['Total Qty Day'] = data['Inbound from PO'] + data['Start Available Stock']
    data['Date'] = pd.to_datetime(data['Date'])
    data['Week'] = data['Date'] - pd.to_timedelta(data['Date'].dt.weekday, unit='D')
    data['Month'] = data['Date'].dt.strftime('%Y-%m')
    
    weekly_max = data.groupby(['Product ID', 'Week'])['Total Qty Day'].max().reset_index()
    monthly_max = data.groupby(['Product ID', 'Month'])['Total Qty Day'].max().reset_index()
    product_mapping = data[['Product ID', 'Product Name']].drop_duplicates().set_index('Product ID')['Product Name'].to_dict()
    
    return weekly_max, monthly_max, product_mapping, data

weekly_max, monthly_max, product_mapping, full_data = preprocess_data()

# Sidebar filter for Pareto classification
pareto_options = full_data['New Pareto A-D (Monthly)'].dropna().unique()
selected_pareto = st.sidebar.selectbox("Select Pareto Class", pareto_options)

# Filter products based on selected Pareto class
filtered_products = full_data.loc[full_data['New Pareto A-D (Monthly)'] == selected_pareto, 'Product ID'].unique()
product_id = st.sidebar.selectbox("Select Product ID", filtered_products)

timeframe = st.sidebar.radio("Select Timeframe", ['Weekly', 'Monthly'])

# Product name
title_product_name = product_mapping.get(product_id, "Unknown Product")
st.subheader(f"📌 Product: {title_product_name} (ID: {product_id})")

# Filter data
if timeframe == 'Weekly':
    data = weekly_max.loc[weekly_max['Product ID'] == product_id, ['Week', 'Total Qty Day']]
    x_col = 'Week'
else:
    data = monthly_max.loc[monthly_max['Product ID'] == product_id, ['Month', 'Total Qty Day']]
    x_col = 'Month'

# Limit number of points
data = data.sort_values(x_col).iloc[-50:]

# Plot
fig = px.line(data, x=x_col, y='Total Qty Day', 
              title=f'Max Total Qty for {title_product_name} ({product_id})', markers=True)
st.plotly_chart(fig)

