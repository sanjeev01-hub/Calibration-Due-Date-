import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta
from PIL import Image


# Set the page configuration to wide layout
st.set_page_config(layout="wide")

# Function to send notification using Pushbullet
def send_notification(title, body):
    ACCESS_TOKEN = "o.FsUlbrJjn2MOWhJTT8GnSV72uzN3Xpbc"  # Replace with your Pushbullet Access Token
    headers = {
        "Access-Token": ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    data = {
        "type": "note",
        "title": title,
        "body": body
    }
    url = "https://api.pushbullet.com/v2/pushes"
    response = requests.post(url, headers=headers, json=data)
    response_json = response.json()  # Convert response to JSON

    if response.status_code == 200:
        st.success("Notification sent successfully!")
    else:
        st.error(f"Failed to send notification. Status code: {response.status_code}")
        st.write(response_json)  # Display error response for debugging

# Custom CSS for styling
st.markdown("""
    <style>
    .reportview-container {
        background: #f0f2f6;
    }
    .sidebar .sidebar-content {
        background: #ffffff;
    }
    .stButton>button {
        color: #ffffff;
        background-color: #007bff;
        border-radius: 8px;
        border: 1px solid #007bff;
    }
    </style>
    """, unsafe_allow_html=True)
col1, col2 = st.columns([1, 4])
with col1:
        image = Image.open('t.png')
        st.image(image)
        
with col2:
        st.write('Sanjeev Kumar Sharma(VT20243942) ')

st.title("Calibration Due Date And Monitoring System Dashboard")

# Upload CSV file
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    # Load the CSV file
    data = pd.read_csv(uploaded_file)

    # Clean up column names
    data.columns = data.columns.str.replace(r'\s+', ' ', regex=True).str.strip().str.replace('\n', ' ', regex=False).str.replace('.', '', regex=False)

    # Display the column names for debugging purposes
    #st.write("Column Names:", data.columns.tolist())

    # Preprocessing dates
    try:
        data['Cal Date'] = pd.to_datetime(data['Cal Date'], format='%d/%m/%Y', errors='coerce')
        data['Due Date'] = pd.to_datetime(data['Due Date'], format='%d/%m/%Y', errors='coerce')
    except Exception as e:
        st.error(f"Error parsing dates: {e}")
        st.stop()

    # Show raw data
    if st.checkbox("Show raw data"):
        st.write(data)

    # Summary metrics
    st.header("Summary Metrics")
    total_equipments = data.shape[0]
    calibrated = (data['Calibration Status'] == 'OK').sum()
    due_for_calibration = (data['Calibration Status'] == 'Due').sum()
    out_for_calibration = (data['Calibration Status'] == 'Out for Calibration').sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Equipments", total_equipments)
    col2.metric("Calibrated", calibrated)
    col3.metric("Due for Calibration", due_for_calibration)
    col4.metric("Out for Calibration", out_for_calibration)

    # Check for products out of calibration and notify if due date is past or within next 10 days
    today = datetime.now().date()
    due_within_10_days = data[(data['Due Date'].dt.date >= today) & (data['Due Date'].dt.date <= today + timedelta(days=10))]
    overdue = data[data['Due Date'].dt.date < today]

    if not due_within_10_days.empty:
        due_within_10_days_display = due_within_10_days[['Id No', 'Equipment Name', 'Due Date']]  # Adjust column name here
        if not due_within_10_days_display.empty:
            st.warning("Products due for calibration within the next 10 days:")
            st.write(due_within_10_days_display)
            
            # Send notifications for products due within 10 days
            for index, row in due_within_10_days_display.iterrows():
                send_notification(f"Equipment '{row['Equipment Name']}' (ID: {row['Id No']}) due for calibration soon!", f"Due Date: {row['Due Date'].strftime('%d/%m/%Y')}")

        else:
            st.warning("No products due for calibration within the next 10 days.")

    if not overdue.empty:
        overdue_display = overdue[['Id No', 'Equipment Name', 'Due Date']]  # Adjust column name here
        if not overdue_display.empty:
            st.error("Overdue products for calibration:")
            st.write(overdue_display)
            
            # Send notifications for overdue products
            for index, row in overdue_display.iterrows():
                send_notification(f"Equipment '{row['Equipment Name']}' (ID: {row['Id No']}) is overdue for calibration!", f"Due Date: {row['Due Date'].strftime('%d/%m/%Y')}")

        else:
            st.error("No overdue products for calibration found.")

    # Stock Monitoring Section
    st.header("Stock Monitoring")

    # Filter products with stock <= 10
    low_stock_products = data[data['Stock'] <= 10]

    if not low_stock_products.empty:
        st.warning("Products with low stock (<= 10):")
        st.write(low_stock_products[['Id No', 'Equipment Name', 'Stock']])  # Adjust column name here
        
        # Send notifications for low stock products
        for index, row in low_stock_products.iterrows():
            send_notification(f"Equipment '{row['Equipment Name']}' (ID: {row['Id No']}) has low stock!", f"Current Stock: {row['Stock']}")

    else:
        st.success("All products have sufficient stock.")

    # Arrange two graphs in one row
    with st.container():
        col1, col2 = st.columns(2)

        with col1:
            # Bar chart for calibration status
            st.header("Calibration Status")
            calibration_status_counts = data['Calibration Status'].value_counts()
            fig1 = px.bar(calibration_status_counts, x=calibration_status_counts.index, y=calibration_status_counts.values, labels={'x': 'Calibration Status', 'y': 'Count'}, title="Calibration Status Distribution", color=calibration_status_counts.index, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            # Bar chart for availability status
            st.header("Availability Status")
            availability_status_counts = data['Availability Status'].value_counts()
            fig2 = px.bar(availability_status_counts, x=availability_status_counts.index, y=availability_status_counts.values, labels={'x': 'Availability Status', 'y': 'Count'}, title="Availability Status Distribution", color=availability_status_counts.index, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig2, use_container_width=True)

    # Remaining graphs in another row
    with st.container():
        # Pie chart for outward location
        st.header("Outward Location Distribution")
        outward_location_counts = data['Outward Location'].value_counts()
        fig3 = px.pie(outward_location_counts, names=outward_location_counts.index, values=outward_location_counts.values, title="Outward Location Distribution", color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig3, use_container_width=True)

        # Additional graph for calibration status over due dates
        st.header("Calibration Status Over Due Dates")
        fig4 = px.histogram(data, x='Due Date', color='Calibration Status', title="Calibration Status Over Due Dates", labels={'Due Date': 'Due Date', 'count': 'Count'}, barmode='group')
        st.plotly_chart(fig4, use_container_width=True)

        # Filter data by calibration status
        st.header("Filter by Calibration Status")
        status_filter = st.selectbox("Select Calibration Status", options=data['Calibration Status'].unique())
        filtered_data = data[data['Calibration Status'] == status_filter]
        st.write(filtered_data)

        # Line chart for calibration due dates
        st.header("Calibration Due Dates Over Time")
        data_sorted_by_due_date = data.sort_values('Due Date')

        # Check if 'Id No' column exists and plot accordingly
        if 'Id No' in data.columns:
            fig5 = px.line(data_sorted_by_due_date, x='Due Date', y='Id No', title="Calibration Due Dates Over Time", markers=True)
            st.plotly_chart(fig5, use_container_width=True)
        else:
            st.error("Column 'Id No' not found in the dataset. Please check the CSV file for the correct column name.")
else:
    st.write("Please upload a CSV file to proceed.")
