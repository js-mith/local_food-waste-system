import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime, date

# 🎨 Custom CSS for background color & styling
page_bg_css = """
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(to right, #ffecd2, #fcb69f);
}
[data-testid="stHeader"] {
    background-color: rgba(0,0,0,0);
}
[data-testid="stSidebar"] {
    background: #f6f6f6;
}
</style>
"""
st.markdown(page_bg_css, unsafe_allow_html=True)

# Database path
DB_PATH = "food_waste.db"

# ✅ Create DB if not exists using CSVs
def create_database():
    conn = sqlite3.connect(DB_PATH)
    # Load CSVs
    providers_df = pd.read_csv("providers_data.csv")
    receivers_df = pd.read_csv("receivers_data.csv")
    food_df = pd.read_csv("food_listings_data.csv")
    claims_df = pd.read_csv("claims_data.csv")

    # Save to SQL
    providers_df.to_sql("providers", conn, if_exists="replace", index=False)
    receivers_df.to_sql("receivers", conn, if_exists="replace", index=False)
    food_df.to_sql("food_listings", conn, if_exists="replace", index=False)
    claims_df.to_sql("claims", conn, if_exists="replace", index=False)

    conn.close()

if not os.path.exists(DB_PATH):
    create_database()

# DB helpers
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def run_query(query, params=()):
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def run_action(query, params=()):
    conn = get_connection()
    conn.execute(query, params)
    conn.commit()
    conn.close()

# Page config
st.set_page_config(page_title="Local Food Wastage Management", layout="wide")
st.title("🍲 Local Food Wastage Management System")

# Sidebar menu
menu = st.sidebar.radio("Navigation", ["Home", "View Data", "Analytics", "Add Listing", "Update Listing", "Delete Listing"])

# Home
if menu == "Home":
    st.subheader("Welcome!")
    st.write("""
        This Streamlit app connects food providers and receivers to reduce food waste.
        You can:
        - View providers, receivers, listings, and claims
        - Analyze trends
        - Add, update, and delete listings
    """)

# View Data
elif menu == "View Data":
    table = st.selectbox("Select Table", ["providers", "receivers", "food_listings", "claims"])
    df = run_query(f"SELECT * FROM {table}")
    st.dataframe(df)

# Analytics
elif menu == "Analytics":
    st.subheader("📊 Key Insights")

    st.write("### Providers & Receivers per City")
    q1 = """
    SELECT City,
           SUM(providers_count) AS Providers,
           SUM(receivers_count) AS Receivers
    FROM (
        SELECT City, COUNT(*) AS providers_count, 0 AS receivers_count FROM providers GROUP BY City
        UNION ALL
        SELECT City, 0, COUNT(*) FROM receivers GROUP BY City
    )
    GROUP BY City
    ORDER BY City;
    """
    st.dataframe(run_query(q1))

    st.write("### Most Common Food Types")
    q7 = """
    SELECT Food_Type, COUNT(*) AS Count_Listings
    FROM food_listings
    GROUP BY Food_Type
    ORDER BY Count_Listings DESC;
    """
    st.dataframe(run_query(q7))

    st.write("### Claims Status Distribution")
    q10 = """
    SELECT Status, COUNT(*) AS Count_Status,
           ROUND(100.0*COUNT(*)/(SELECT COUNT(*) FROM claims),2) AS Percentage
    FROM claims
    GROUP BY Status;
    """
    df_status = run_query(q10)
    st.dataframe(df_status)
    st.bar_chart(df_status.set_index("Status")["Count_Status"])

# Add Listing
elif menu == "Add Listing":
    st.subheader("Add a New Food Listing")
    Food_Name = st.text_input("Food Name")
    Quantity = st.number_input("Quantity", min_value=1, step=1)
    Expiry_Date = st.date_input("Expiry Date", min_value=date.today())
    Provider_ID = st.number_input("Provider ID", min_value=1, step=1)
    Provider_Type = st.text_input("Provider Type")
    Location = st.text_input("Location")
    Food_Type = st.text_input("Food Type")
    Meal_Type = st.text_input("Meal Type")

    if st.button("Add Listing"):
        run_action("""
            INSERT INTO food_listings (Food_Name, Quantity, Expiry_Date, Provider_ID, Provider_Type, Location, Food_Type, Meal_Type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (Food_Name, Quantity, Expiry_Date.isoformat(), Provider_ID, Provider_Type, Location, Food_Type, Meal_Type))
        st.success("Food listing added successfully!")

# Update Listing
elif menu == "Update Listing":
    st.subheader("Update an Existing Food Listing")
    df_listings = run_query("SELECT Food_ID, Food_Name FROM food_listings")
    listing_ids = df_listings["Food_ID"].tolist()
    selected_id = st.selectbox("Select Food ID to Update", listing_ids)

    if selected_id:
        current_data = run_query("SELECT * FROM food_listings WHERE Food_ID = ?", (selected_id,))
        if not current_data.empty:
            row = current_data.iloc[0]
            Food_Name = st.text_input("Food Name", row["Food_Name"])
            Quantity = st.number_input("Quantity", min_value=1, step=1, value=row["Quantity"])
            Expiry_Date = st.date_input("Expiry Date", value=date.fromisoformat(row["Expiry_Date"]) if row["Expiry_Date"] else date.today())
            Provider_ID = st.number_input("Provider ID", min_value=1, step=1, value=row["Provider_ID"])
            Provider_Type = st.text_input("Provider Type", row["Provider_Type"])
            Location = st.text_input("Location", row["Location"])
            Food_Type = st.text_input("Food Type", row["Food_Type"])
            Meal_Type = st.text_input("Meal Type", row["Meal_Type"])

            if st.button("Update Listing"):
                run_action("""
                    UPDATE food_listings
                    SET Food_Name=?, Quantity=?, Expiry_Date=?, Provider_ID=?, Provider_Type=?, Location=?, Food_Type=?, Meal_Type=?
                    WHERE Food_ID=?
                """, (Food_Name, Quantity, Expiry_Date.isoformat(), Provider_ID, Provider_Type, Location, Food_Type, Meal_Type, selected_id))
                st.success("Food listing updated successfully!")

# Delete Listing
elif menu == "Delete Listing":
    st.subheader("Delete a Food Listing")
    df_listings = run_query("SELECT Food_ID, Food_Name FROM food_listings")
    listing_ids = df_listings["Food_ID"].tolist()
    selected_id = st.selectbox("Select Food ID to Delete", listing_ids)

    if st.button("Delete Listing"):
        run_action("DELETE FROM food_listings WHERE Food_ID=?", (selected_id,))
        st.success(f"Food listing with ID {selected_id} deleted.")
