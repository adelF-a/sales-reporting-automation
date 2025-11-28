import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# Configuration
num_rows = 5000
products = ['Enterprise License', 'Consulting Service', 'Basic Support', 'Premium Maintenance']
regions = ['North America', 'Europe', 'Asia-Pacific', 'Latin America']
start_date = datetime(2024, 1, 1)

print("Generating synthetic sales data...")

# Generate Lists
data = {
    'Transaction_ID': [f'TRX-{10000+i}' for i in range(num_rows)],
    'Date': [start_date + timedelta(days=random.randint(0, 365)) for _ in range(num_rows)],
    'Region': [random.choice(regions) for _ in range(num_rows)],
    'Product': [random.choice(products) for _ in range(num_rows)],
    'Quantity': [random.randint(1, 20) for _ in range(num_rows)],
    'Unit_Price': [],
    'Unit_Cost': []
}

# Apply Business Logic (Price vs Cost)
for p in data['Product']:
    if p == 'Enterprise License':
        data['Unit_Price'].append(1200.00)
        data['Unit_Cost'].append(50.00)  # High Margin
    elif p == 'Consulting Service':
        data['Unit_Price'].append(150.00)
        data['Unit_Cost'].append(100.00) # Low Margin
    elif p == 'Basic Support':
        data['Unit_Price'].append(300.00)
        data['Unit_Cost'].append(50.00)
    else: # Premium Maintenance
        data['Unit_Price'].append(600.00)
        data['Unit_Cost'].append(200.00)

df = pd.DataFrame(data)

# Inject "Dirty Data" (Missing Regions) - To demonstrate Cleaning Skills
# We randomly delete 150 region values
random_indices = np.random.choice(df.index, size=150, replace=False)
df.loc[random_indices, 'Region'] = np.nan

# Save to CSV
output_path = 'data/raw_sales_data.csv'
df.to_csv(output_path, index=False)
print(f"✅ Success! Generated {num_rows} rows at '{output_path}'")