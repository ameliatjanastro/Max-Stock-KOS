import pandas as pd
import plotly.express as px
import streamlit as st

# Streamlit title
st.title("📊 Stock Analysis Dashboard")

# Load and optimize data
@st.cache_data
def preprocess_data():
    data = pd.read_excel('stock kos.xlsx', usecols=['Date', 'Product ID', 'Product Name', 
                                                    'Start Available Stock', 'Inbound from PO', 'Inbound from SO Act Qty'],
                         dtype={'Product ID': 'category', 'Product Name': 'string'})

    for col in ['Start Available Stock', 'Inbound from PO', 'Inbound from SO Act Qty']:
        data[col] = pd.to_numeric(data[col], downcast='float')

    data['Total Qty Day'] = data['Inbound from PO'] + data['Start Available Stock']
    data['Date'] = pd.to_datetime(data['Date'])
    data['Week Start'] = data['Date'] - pd.to_timedelta(data['Date'].dt.weekday, unit='D')
    data['Month'] = data['Date'].dt.strftime('%Y-%m')

    weekly_max = data.groupby(['Product ID', 'Week Start'])['Total Qty Day'].max().reset_index()
    monthly_max = data.groupby(['Product ID', 'Month'])['Total Qty Day'].max().reset_index()
    product_mapping = data[['Product ID', 'Product Name']].drop_duplicates().set_index('Product ID')['Product Name'].to_dict()

    return weekly_max, monthly_max, product_mapping

weekly_max, monthly_max, product_mapping = preprocess_data()

# Sidebar selection
product_id = st.sidebar.selectbox("Select Product ID", weekly_max['Product ID'].unique())
timeframe = st.sidebar.radio("Select Timeframe", ['Weekly', 'Monthly'])

# Product name
product_name = product_mapping.get(product_id, "Unknown Product")
st.subheader(f"📌 Product: {product_name} (ID: {product_id})")

# Filter data
if timeframe == 'Weekly':
    data = weekly_max.loc[weekly_max['Product ID'] == product_id, ['Week Start', 'Total Qty Day']]
    x_col = 'Week Start'
else:
    data = monthly_max.loc[monthly_max['Product ID'] == product_id, ['Month', 'Total Qty Day']]
    x_col = 'Month'

# Limit number of points
data = data.sort_values(x_col).iloc[-50:]

# Plot
fig = px.line(data, x=x_col, y='Total Qty Day', 
              title=f'Max Total Qty for {product_name} ({product_id})', markers=True)
st.plotly_chart(fig)
