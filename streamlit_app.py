import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st

# Disable chained assignment warnings
pd.options.mode.chained_assignment = None  

# Load data
data = pd.read_csv('stock_kos.csv', delimiter=";", engine="python")

# Select relevant columns
stock = data[['Date', 'Product ID', 'Product Name', 'Start Available Stock', 'Inbound from PO', 'Inbound from SO Act Qty']]
stock['Total Qty Day'] = stock['Inbound from PO'] + stock['Start Available Stock']

# Convert date column to datetime format
stock['Date'] = pd.to_datetime(stock['Date'])

# Calculate start of the week (Monday)
stock['Week Start'] = stock['Date'] - pd.to_timedelta(stock['Date'].dt.weekday, unit='D')

# Extract month in YYYY-MM format
stock['Month'] = stock['Date'].dt.strftime('%Y-%m')

# Aggregate max total stock per week and per month
weekly_max = stock.groupby(['Product ID', 'Week Start'])['Total Qty Day'].max().reset_index()
monthly_max = stock.groupby(['Product ID', 'Month'])['Total Qty Day'].max().reset_index()

# Create dictionary mapping Product ID to Product Name
product_mapping = stock[['Product ID', 'Product Name']].drop_duplicates().set_index('Product ID')['Product Name'].to_dict()

# Streamlit UI
st.title("📊 Stock Analysis Dashboard")

# Sidebar filters
product_id = st.sidebar.selectbox("Select Product ID", stock['Product ID'].unique())
timeframe = st.sidebar.radio("Select Timeframe", ['Weekly', 'Monthly'])

# Get product name
product_name = product_mapping.get(product_id, "Unknown Product")

# Filter data based on selection
if timeframe == 'Weekly':
    data = weekly_max[weekly_max['Product ID'] == product_id]
    x_col = 'Week Start'
else:
    data = monthly_max[monthly_max['Product ID'] == product_id]
    x_col = 'Month'

# Display product name
st.subheader(f"📌 Product: {product_name} (ID: {product_id})")

# Create plot
fig = px.line(data, x=x_col, y='Total Qty Day', 
              title=f'Max Total Qty for {product_name} ({product_id})', markers=True)

# Show plot
st.plotly_chart(fig)
