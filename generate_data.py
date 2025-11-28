import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# Configuration for synthetic data generation
num_transactions = 5000
num_customers = 500  
products = ['Enterprise License', 'Consulting Service', 'Basic Support', 'Premium Maintenance']
regions = ['North America', 'Europe', 'Asia-Pacific', 'Latin America']
start_date = datetime(2023, 1, 1)

print("Initializing data generation...")

# Generate a fixed list of unique Customer IDs
customer_ids = [f'CUST-{100+i}' for i in range(num_customers)]

# Initialize dictionary for DataFrame construction
data = {
    'Transaction_ID': [f'TRX-{10000+i}' for i in range(num_transactions)],
    'Date': [],
    'Customer_ID': [], 
    'Region': [],
    'Product': [],
    'Quantity': [],
    'Unit_Price': [],
    'Unit_Cost': []
}

# Populate data with randomized values
for _ in range(num_transactions):
    # Create a weighted date distribution (more sales in recent months)
    days_offset = int(np.random.beta(5, 2) * 365) 
    date = start_date + timedelta(days=days_offset)
    
    # Assign random attributes
    cust = random.choice(customer_ids)
    region = random.choice(regions) 
    prod = random.choice(products)
    
    data['Date'].append(date)
    data['Customer_ID'].append(cust)
    data['Region'].append(region)
    data['Product'].append(prod)
    data['Quantity'].append(random.randint(1, 10))

    # Define pricing logic based on product type
    if prod == 'Enterprise License':
        data['Unit_Price'].append(1200.00); data['Unit_Cost'].append(50.00)
    elif prod == 'Consulting Service':
        data['Unit_Price'].append(150.00); data['Unit_Cost'].append(100.00)
    elif prod == 'Basic Support':
        data['Unit_Price'].append(300.00); data['Unit_Cost'].append(50.00)
    else:
        data['Unit_Price'].append(600.00); data['Unit_Cost'].append(200.00)

df = pd.DataFrame(data)

# Introduce missing values in 'Region' to simulate real-world dirty data
# These will be handled in the ETL pipeline later
random_indices = np.random.choice(df.index, size=150, replace=False)
df.loc[random_indices, 'Region'] = np.nan

# Export raw data to CSV
output_path = 'data/raw_sales_data.csv'
df.to_csv(output_path, index=False)
print(f"✅ Data generation complete. Saved to '{output_path}'")