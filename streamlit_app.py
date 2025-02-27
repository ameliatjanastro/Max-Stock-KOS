import pandas as pd
import plotly.express as px
import streamlit as st

# Title (smaller than st.title)
st.markdown("<h3 style='text-align: left;'>🏭  Beginning Stock + Max Inbound PO Qty</h3>", unsafe_allow_html=True)

# Streamlit title
#st.header("🏭  Beginning Stock + Max Inbound PO Qty")

# Load and optimize data
@st.cache_data
def preprocess_data():
    # Load stock data
    stock_data = pd.read_excel('stock kos.xlsx', usecols=['Date', 'Product ID', 'Product Name',
                                                          'Start Available Stock', 'Inbound from PO', 'Inbound from SO Act Qty'],
                               dtype={'Product ID': 'category', 'Product Name': 'string'})
    
    # Load Pareto classification
    pareto_data = pd.read_excel('dash_jan pareto.xlsx', usecols=['Product ID', 'New Pareto A-D (Monthly)'],
                                 dtype={'Product ID': 'category'})
    
    # Merge datasets
    data = stock_data.merge(pareto_data, on='Product ID', how='left')

    # Define the custom order for Pareto classes
    pareto_order = ["X", "A", "B", "C", "D", "New SKU A", "New SKU B", "New SKU C", "New SKU D", "No Sales L3M"]

    # Convert the Pareto column to categorical with the custom order
    data["New Pareto A-D (Monthly)"] = pd.Categorical(
        data["New Pareto A-D (Monthly)"], 
        categories=pareto_order, 
        ordered=True
    )

    # Sort data based on Pareto class order
    data = data.sort_values("New Pareto A-D (Monthly)")
    
    for col in ['Start Available Stock', 'Inbound from PO', 'Inbound from SO Act Qty']:
        data[col] = pd.to_numeric(data[col], downcast='float')
    
    data['Max Total Qty Daily (Beginning + PO)'] = data['Inbound from PO'] + data['Start Available Stock']
    data['Date'] = pd.to_datetime(data['Date'])
    data['Week'] = data['Date'] - pd.to_timedelta(data['Date'].dt.weekday, unit='D')
    data['Month'] = data['Date'].dt.to_period('M') 
    data['Month_str'] = data['Month'].dt.strftime('%b-%y')
    
    weekly_max = data.groupby(['Product ID', 'Week'])['Max Total Qty Daily (Beginning + PO)'].max().reset_index()
    monthly_max = data.groupby(['Product ID', 'Month'])['Max Total Qty Daily (Beginning + PO)'].max().reset_index()
    # Ensure sorting by proper date
    monthly_max = monthly_max.sort_values(by="Month")
    monthly_max['Month'] = monthly_max['Month'].astype(str)
    product_mapping = data[['Product ID', 'Product Name']].drop_duplicates().set_index('Product ID')['Product Name'].to_dict()
    
    return weekly_max, monthly_max, product_mapping, data

weekly_max, monthly_max, product_mapping, data = preprocess_data()

# Sidebar filter for Pareto classification
pareto_options = data['New Pareto A-D (Monthly)'].dropna().unique()
selected_pareto = st.sidebar.selectbox("Select Pareto Class", pareto_options)

# Filter products based on selected Pareto class
filtered_products_info = data.loc[data['New Pareto A-D (Monthly)'] == selected_pareto, ['Product ID', 'Product Name']]
filtered_products_info = filtered_products_info.drop_duplicates()

# Get total count of products under the selected Pareto class
total_products = len(filtered_products_info)

# Display total product count
st.sidebar.markdown(f"**Total Products in {selected_pareto}: {total_products}**")

# Create a dropdown format "Product ID - Product Name"
filtered_products_info['Dropdown Label'] = filtered_products_info['Product ID'].astype(str) + " - " + filtered_products_info['Product Name']

# Map the selection back to Product ID
product_dict = dict(zip(filtered_products_info['Dropdown Label'], filtered_products_info['Product ID']))

# Sidebar searchable dropdown for selecting Product
selected_label = st.sidebar.selectbox("Select Product", options=filtered_products_info['Dropdown Label'], index=0)

# Extract the selected Product ID
product_id = product_dict[selected_label]

# Sidebar radio button for timeframe selection
timeframe = st.sidebar.radio("Select Timeframe", ['Weekly', 'Monthly'])

# Product name
title_product_name = product_mapping.get(product_id, "Unknown Product")
#st.markdown(f"<h5> Product: {title_product_name} (ID: {product_id})</h5>", unsafe_allow_html=True)

# Use st.empty() to only refresh the graph
graph_placeholder = st.empty()

# Filter data
if timeframe == 'Weekly':
    data = weekly_max.loc[weekly_max['Product ID'] == product_id, ['Week', 'Max Total Qty Daily (Beginning + PO)']]
    x_col = 'Week'
else:
    data = monthly_max.loc[monthly_max['Product ID'] == product_id, ['Month', 'Max Total Qty Daily (Beginning + PO)']]
    x_col = 'Month'

# Limit number of points
data = data.sort_values(x_col).iloc[-50:]

# Plot
fig = px.line(data, x=x_col, y='Max Total Qty Daily (Beginning + PO)', 
              title=f'Max Total Qty for {title_product_name} ({product_id})', markers=True)

# Set x-axis tick format dynamically
fig.update_layout(
    height=350,  # Reduce height slightly
    margin=dict(l=10, r=10, t=30, b=10),
    xaxis=dict(
        tickformat="%b %Y" if timeframe == 'Monthly' else "%d %b %Y"
    )
)

# Make marker values bold
# Manually add bold annotations for marker values
for i, row in data.iterrows():
    qty = int(row['Max Total Qty Daily (Beginning + PO)'])
    fig.add_annotation(
        x=row[x_col], 
        y=row['Max Total Qty Daily (Beginning + PO)'], 
        text=f"<b>{qty}</b>",  # No decimals
        showarrow=False, 
        font=dict(size=10, color="black"),
        bgcolor="rgba(255, 255, 255, 0.7)",
        yshift=10  # Move text slightly above the marker
    )

# Refresh only the graph, not the whole UI
graph_placeholder.empty()
graph_placeholder.plotly_chart(fig, use_container_width=True)

