import pandas as pd
import sqlite3

# Database description
DB_DESCRIPTION = """
The database contains a single table named 'Retail' with the following columns:
- Customer_ID: Unique identifier for each customer
- Name: Customer's name
- Gender: Customer's gender (Male/Female)
- Age: Customer's age
- Country: Customer's country of residence
- State: Customer's state of residence
- City: Customer's city of residence
- Zip_Code: Customer's zip code
- Product: Name of the product purchased
- Category: Category of the product
- Price: Price of the product
- Purchase_Date: Date of purchase
- Quantity: Quantity of the product purchased
- Total_Spent: Total amount spent on the purchase
"""

def create_sample_data():
    data = {
        "Customer_ID": range(1, 101),
        "Name": [f"Customer {i}" for i in range(1, 101)],
        "Gender": ["Male", "Female"] * 50,
        "Age": [20 + i % 60 for i in range(100)],
        "Country": ["USA", "Canada"] * 50,
        "State": ["CA", "NY", "ON", "BC"] * 25,
        "City": ["Los Angeles", "New York", "Toronto", "Vancouver"] * 25,
        "Zip_Code": [f"{90000 + i}" for i in range(100)],
        "Product": [f"Product {i}" for i in range(1, 101)],
        "Category": ["Electronics", "Clothing", "Books", "Home"] * 25,
        "Price": [10 + i * 5 for i in range(100)],
        "Purchase_Date": pd.date_range(start="2023-01-01", periods=100).strftime("%Y-%m-%d").tolist(),
        "Quantity": [1 + i % 5 for i in range(100)],
        "Total_Spent": [0] * 100  # We'll calculate this
    }
    
    df = pd.DataFrame(data)
    df["Total_Spent"] = df["Price"] * df["Quantity"]
    return df

def initialize_database():
    conn = sqlite3.connect('retail.db')
    df = create_sample_data()
    df.to_sql('Retail', conn, if_exists='replace', index=False)
    conn.close()
    print("Database initialized with sample data.")

def query_db(query):
    conn = sqlite3.connect('retail.db')
    try:
        return pd.read_sql_query(query, conn)
    finally:
        conn.close()

if __name__ == "__main__":
    initialize_database()